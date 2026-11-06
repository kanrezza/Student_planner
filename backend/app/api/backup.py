"""/api/backup/* (feature 003, contracts/rest-api.md): cấu hình, trạng thái, việc cho agent,
tạo bản sao lưu và khôi phục."""

import logging
import shutil
import tempfile
from pathlib import Path

from flask import Blueprint, request, send_file

from app import config as app_config
from app.api.errors import ApiError
from app.extensions import db
from app.schemas.backup import (
    AgentReportIn,
    BackupConfigPatch,
    JobCreate,
    JobUpdate,
)
from app.services import backup, backup_jobs

bp = Blueprint("backup", __name__)
log = logging.getLogger(__name__)


def _json() -> dict:
    return request.get_json(silent=True) or {}


@bp.get("/backup/status")
def get_status():
    return backup_jobs.status_view()


@bp.get("/backup/config")
def get_config():
    return backup_jobs.config_view(backup_jobs.get_config())


@bp.patch("/backup/config")
def patch_config():
    patch = BackupConfigPatch.model_validate(_json())
    return backup_jobs.config_view(backup_jobs.update_config(patch))


@bp.post("/backup/jobs")
def create_job():
    job = backup_jobs.create_job(JobCreate.model_validate(_json()))
    return backup_jobs.job_view(job), 201


@bp.post("/backup/jobs/claim")
def claim_job():
    job = backup_jobs.claim_job()
    return (backup_jobs.job_view(job), 200) if job else ("", 204)


@bp.put("/backup/jobs/<int:job_id>")
def put_job(job_id: int):
    job = backup_jobs.update_job(job_id, JobUpdate.model_validate(_json()))
    return backup_jobs.job_view(job)


@bp.put("/backup/agent-report")
def put_agent_report():
    backup_jobs.apply_agent_report(AgentReportIn.model_validate(_json()))
    return "", 204


@bp.get("/backup/dump")
def get_dump():
    built = backup.build_backup(request.args.get("kind", "thu-cong"))
    response = send_file(
        built.path,
        mimetype="application/zip",
        as_attachment=True,
        download_name=built.name,
    )
    response.headers["X-Backup-Name"] = built.name
    response.headers["X-Backup-Sha256"] = built.sha256
    response.call_on_close(built.cleanup)
    return response


@bp.post("/backup/restore")
def post_restore():
    request.max_content_length = app_config.MAX_RESTORE_BYTES
    workdir = Path(tempfile.mkdtemp(prefix="lichhoc-upload-"))
    try:
        upload = workdir / "upload.lhbackup"
        with upload.open("wb") as handle:
            shutil.copyfileobj(request.stream, handle, 1 << 20)
        if upload.stat().st_size == 0:
            raise ApiError(400, "backup_corrupt", "Bản sao lưu bị hỏng, không thể khôi phục")
        result = backup.restore_backup(upload)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        db.session.remove()
    return {"restored": True, **result}
