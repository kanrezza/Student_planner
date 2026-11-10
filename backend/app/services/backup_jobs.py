"""Cấu hình, trạng thái và việc giao cho agent (feature 003, data-model §1)."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select

from app.api.errors import ApiError
from app.extensions import db
from app.lib import timeutil
from app.lib.timeutil import iso
from app.models import BackupConfig, BackupJob, BackupStatus
from app.models.backup import ACTIVE_JOB_STATES
from app.schemas.backup import AgentReportIn, BackupConfigPatch, JobCreate, JobUpdate
from app.services.revision import bump_revision

STALE_AFTER = timedelta(days=3)
AGENT_OFFLINE_AFTER = timedelta(minutes=2)
JOB_STUCK_AFTER = timedelta(minutes=30)
RECENT_JOB_WINDOW = timedelta(hours=1)
DEFAULT_DISPLAY = "iCloud Drive › Lịch Học Cá Nhân › Sao lưu"
ICLOUD_MARKER = "/com~apple~CloudDocs/"


def get_config() -> BackupConfig:
    return db.session.get(BackupConfig, 1)


def config_revision(config: BackupConfig) -> int:
    """Số tăng mỗi lần cấu hình đổi, để agent biết khi nào cần đọc lại."""
    return int(config.updated_at.timestamp() * 1000)


def config_view(config: BackupConfig) -> dict:
    return {
        "enabled": config.enabled,
        "schedule_time": config.schedule_time.strftime("%H:%M"),
        "destination_path": config.destination_path,
        "destination_display": destination_display(config.destination_path),
        "retention_count": config.retention_count,
        "enabled_since": iso(config.enabled_since),
    }


def destination_display(path: str | None) -> str:
    """Đường dẫn dễ đọc: iCloud Drive › A › B, hoặc Ổ › A › B cho /Volumes/Ổ/A/B."""
    if path is None:
        return DEFAULT_DISPLAY
    if ICLOUD_MARKER in path:
        rest = path.split(ICLOUD_MARKER, 1)[1].strip("/")
        return " › ".join(["iCloud Drive", *rest.split("/")]) if rest else "iCloud Drive"
    if path.startswith("/Volumes/"):
        return " › ".join(part for part in path[len("/Volumes/") :].split("/") if part)
    return path


def update_config(patch: BackupConfigPatch) -> BackupConfig:
    config = get_config()
    changes = patch.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is None and field != "destination_path":
            continue  # chỉ destination_path nhận null (= mặc định)
        setattr(config, field, value)
    if changes.get("enabled") is True:
        config.enabled_since = timeutil.now()
    config.updated_at = timeutil.now()
    bump_revision(db.session)
    db.session.commit()
    return config


def apply_agent_report(report: AgentReportIn) -> None:
    status = db.session.get(BackupStatus, 1)
    data = report.model_dump(exclude={"files"})
    for field, value in data.items():
        setattr(status, field, value)
    status.files = [
        {**f.model_dump(mode="json"), "created_at": iso(f.created_at)} for f in report.files
    ]
    status.reported_at = timeutil.now()
    db.session.commit()


def expire_stuck_jobs(now: datetime) -> None:
    stuck = db.session.scalars(
        select(BackupJob).where(
            BackupJob.state.in_(ACTIVE_JOB_STATES),
            BackupJob.created_at < now - JOB_STUCK_AFTER,
            (BackupJob.started_at.is_(None)) | (BackupJob.started_at < now - JOB_STUCK_AFTER),
        )
    ).all()
    for job in stuck:
        job.state = "failed"
        job.message = "Trình sao lưu không phản hồi"
        job.finished_at = now
    if stuck:
        db.session.commit()


def create_job(data: JobCreate) -> BackupJob:
    now = timeutil.now()
    expire_stuck_jobs(now)
    if data.kind == "restore" and not data.source_path:
        raise ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", {"source_path": "Bắt buộc"})
    active = db.session.scalar(select(BackupJob.id).where(BackupJob.state.in_(ACTIVE_JOB_STATES)))
    if active is not None:
        raise ApiError(409, "job_running", "Đang có một việc sao lưu hoặc khôi phục chạy rồi")
    job = BackupJob(kind=data.kind, source_path=data.source_path, state="pending")
    db.session.add(job)
    bump_revision(db.session)
    db.session.commit()
    return job


def pending_count() -> int:
    return len(db.session.scalars(select(BackupJob.id).where(BackupJob.state == "pending")).all())


def claim_job() -> BackupJob | None:
    job = db.session.scalar(
        select(BackupJob)
        .where(BackupJob.state == "pending")
        .order_by(BackupJob.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if job is None:
        return None
    job.state = "running"
    job.started_at = timeutil.now()
    db.session.commit()
    return job


def update_job(job_id: int, data: JobUpdate) -> BackupJob:
    job = db.session.get(BackupJob, job_id)
    if job is None:
        raise ApiError(404, "not_found", "Không tìm thấy việc sao lưu")
    if job.state not in ACTIVE_JOB_STATES:
        raise ApiError(409, "job_finished", "Việc này đã kết thúc")
    job.state = data.state
    if "step" in data.model_fields_set:
        job.step = data.step
    if "message" in data.model_fields_set:
        job.message = data.message
    if data.state in ("done", "failed"):
        job.finished_at = timeutil.now()
    db.session.commit()
    return job


def job_view(job: BackupJob) -> dict:
    return {
        "id": job.id,
        "kind": job.kind,
        "source_path": job.source_path,
        "state": job.state,
        "step": job.step,
        "message": job.message,
        "created_at": iso(job.created_at),
        "finished_at": iso(job.finished_at) if job.finished_at else None,
    }


def recent_job(now: datetime) -> BackupJob | None:
    return db.session.scalar(
        select(BackupJob)
        .where(BackupJob.created_at > now - RECENT_JOB_WINDOW)
        .order_by(BackupJob.id.desc())
        .limit(1)
    )


def agent_online(status: BackupStatus, now: datetime) -> bool:
    return status.reported_at is not None and now - status.reported_at <= AGENT_OFFLINE_AFTER


def is_stale(config: BackupConfig, status: BackupStatus, now: datetime) -> bool:
    anchor = status.last_success_at or config.enabled_since
    return config.enabled and now - anchor > STALE_AFTER


def _moment(value: datetime | None) -> str | None:
    return iso(value) if value else None


def status_view() -> dict:
    now = timeutil.now()
    expire_stuck_jobs(now)
    config = get_config()
    status = db.session.get(BackupStatus, 1)
    job = recent_job(now)
    return {
        "config": config_view(config),
        "agent_online": agent_online(status, now),
        "destination": {
            "state": status.destination_state,
            "message": status.destination_message,
            "path": status.destination_resolved,
        },
        "last_attempt": {
            "at": _moment(status.last_attempt_at),
            "ok": status.last_attempt_ok,
            "size": status.last_attempt_size,
            "error": status.last_attempt_error,
        },
        "last_success": (
            {"at": iso(status.last_success_at), "size": status.last_success_size}
            if status.last_success_at
            else None
        ),
        "stale": is_stale(config, status, now),
        "files": status.files,
        "job": job_view(job) if job else None,
    }
