/** XMLHttpRequest giả để thử tải file lên (có tiến trình), dùng trong test đính kèm. */
export class FakeXhr {
  static instances: FakeXhr[] = [];
  method = '';
  url = '';
  status = 0;
  responseText = '';
  body: FormData | null = null;
  upload: { onprogress: ((e: unknown) => void) | null } = { onprogress: null };
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onabort: (() => void) | null = null;

  constructor() {
    FakeXhr.instances.push(this);
  }
  open(method: string, url: string) {
    this.method = method;
    this.url = url;
  }
  send(body: FormData) {
    this.body = body;
  }
  abort() {
    this.onabort?.();
  }
  progress(loaded: number, total: number) {
    this.upload.onprogress?.({ lengthComputable: true, loaded, total });
  }
  respond(status: number, json: unknown) {
    this.status = status;
    this.responseText = typeof json === 'string' ? json : JSON.stringify(json);
    this.onload?.();
  }
  static reset() {
    FakeXhr.instances = [];
  }
}
