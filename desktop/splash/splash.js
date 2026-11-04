// Trang chờ: nhận sự kiện `connection-status` từ Rust và gọi lệnh open_orbstack / retry_now.
// Không tải gì từ ngoài; `window.__TAURI__` do Tauri đưa vào (withGlobalTauri).
const { invoke } = window.__TAURI__.core;
const { listen } = window.__TAURI__.event;

const sections = {
  connecting: document.getElementById('connecting'),
  waiting_for_backend: document.getElementById('waiting'),
  orbstack_missing: document.getElementById('missing'),
};

function show(state) {
  for (const [name, el] of Object.entries(sections)) {
    el.hidden = name !== state;
  }
}

document.getElementById('open').addEventListener('click', () => {
  invoke('open_orbstack').catch(() => {});
});
for (const id of ['retry', 'retry-missing']) {
  document.getElementById(id).addEventListener('click', () => invoke('retry_now'));
}

listen('connection-status', (event) => show(event.payload.state)).then(() => {
  // Đăng ký xong mới yêu cầu kiểm tra, để không lỡ trạng thái đã phát trước đó.
  invoke('retry_now');
});
