# Ngữ pháp thêm nhanh tiếng Việt (đợt 2; cụm lặp bật ở đợt 4)

Hàm: `parseQuickAdd(text: string, ctx: QuickParseContext): QuickParse` — kiểu ở
[data-model §2](../data-model.md).

```ts
type QuickParseContext = {
  now: Date;                                   // giờ Việt Nam
  viewDefaultDate: string | null;              // từ quickAddDefaults (feature 002 FR-017): Hôm nay/7 ngày tới → hôm nay; Ngày mai → ngày mai; còn lại null
  tags: {id: number; name: string}[];
  lists: {id: number; name: string; emoji?: string}[];
  dismissed: Set<string>;                      // khoá `${kind}:${start}:${text}`
  recurrence: boolean;                         // false ở đợt 2–3
};
```

## Quy tắc chung

- So khớp trên chuỗi đã gập (`foldVi`: bỏ dấu, `đ→d`, chữ thường); vị trí trả về theo chuỗi gốc.
- Ranh giới từ: trước/sau cụm phải là đầu/cuối chuỗi, khoảng trắng hoặc dấu câu `, . ; : ! ? ( )` (FR-029).
  `#` và `~` phải đứng đầu từ.
- Ưu tiên cụm dài: "thứ 6 tuần sau" > "thứ 6"; "9 giờ 30 tối" > "9 giờ"; "ngày mai" > "mai".
- Mỗi loại chỉ nhận cụm đầu tiên (nhãn: nhận tất cả) (FR-028).
- Cụm bị huỷ (`dismissed`) vẫn trả trong `tokens` với `dismissed: true` để giao diện bỏ tô sáng; không đóng góp
  vào `fields`, giữ lại trong tiêu đề.

## Từ vựng (dạng có dấu; dạng không dấu tương ứng cũng được nhận)

| Loại | Mẫu | Giá trị |
|------|-----|---------|
| date | `hôm nay`, `hnay`, `nay` (chỉ khi đi với buổi: `tối nay`, `sáng nay`) | hôm nay |
| date | `mai`, `ngày mai` | +1 |
| date | `mốt`, `ngày mốt`, `ngày kia` | +2 |
| date | `thứ 2`…`thứ 7`, `thứ hai`…`thứ bảy` (`thứ tư`/`thứ bốn`, `thứ năm`), `T2`…`T7`, `chủ nhật`, `CN` | thứ gần nhất từ hôm nay (FR-028) |
| date | `<thứ> tuần sau`, `<thứ> tuần tới` | thứ đó trong tuần lịch kế tiếp (tuần bắt đầu Thứ Hai) |
| date | `tuần sau`, `tuần tới` | Thứ Hai tuần sau |
| date | `D/M`, `DD/MM`, `D/M/YYYY`, `DD/MM/YYYY` (chỉ dấu `/`; `3-4` trong "Lab 3-4" không phải ngày) | ngày hợp lệ; không năm → năm nay hoặc năm sau nếu đã qua |
| time | `9h`, `9h30`, `9g`, `9g30`, `9:30`, `21:00`, `9 giờ`, `9 giờ 30`, `9 giờ 30 phút`, `9 rưỡi`/`9h rưỡi` | giờ:phút; giờ 0–23, phút 0–59 |
| daypart | `sáng`, `trưa`, `chiều`, `tối`, `đêm` — đứng riêng hoặc ghép với time / `nay` | xem bảng giờ |
| tag | `#<chữ không khoảng trắng>` hoặc tên chọn từ gợi ý | nhãn có sẵn (khớp không dấu) hoặc nhãn mới |
| list | `~<chữ>` hoặc tên chọn từ gợi ý | chỉ danh sách có sẵn |
| important | `*` đứng riêng, `quan trọng` | `is_important = true` |
| priority | `!cao`, `!tb`, `!thấp` | 1, 2, 3 (theo nhãn của app: 1 = Cao, 2 = Trung bình, 3 = Thấp) |
| recurrence | `hằng ngày`, `hàng ngày`, `mỗi ngày` | daily |
| recurrence | `mỗi N ngày` (N 2–365) | every_n_days |
| recurrence | `hằng tuần`, `hàng tuần`, `mỗi tuần` | weekly, thứ của hạn (hoặc hôm nay) |
| recurrence | `<thứ>[, <thứ>…] [và <thứ>] hằng/hàng tuần`, `mỗi <thứ>` | weekly với các thứ đó |
| recurrence | `hằng tháng`, `hàng tháng`, `mỗi tháng`, `ngày D hằng/hàng tháng` | monthly, ngày của hạn hoặc D |

## Buổi trong ngày và "mai" (sửa sau khi dùng thử đợt 2)

- **Buổi** (`sáng`, `trưa`, `chiều`, `tối`, `đêm`) chỉ được hiểu khi **đi sát** (chỉ cách nhau khoảng trắng)
  một giờ ("9h tối", "7 giờ sáng", "sáng 9h") hoặc một cụm ngày ("tối nay", "sáng mai", "chiều thứ 6",
  "thứ 6 chiều", "CN chiều", "sáng mai 9h"). Đứng riêng thì **không** hiểu ("Đi chơi tối" giữ nguyên).
- **Từ ghép không phải buổi**: buổi theo sau bởi tối→(ưu, giản, đa, thiểu, cao, mật…), sáng→(tạo, kiến,
  suốt, chế, lập, tác, giá…), chiều→(chuộng, cao, dài, rộng, sâu, theo, ý…), hoặc đứng sau "ánh" (ánh sáng)
  thì không phải buổi, kể cả khi đi sát một giờ ("9h sáng tạo nội dung" chỉ hiểu 9h).
- **"mai"** đứng một mình là ngày mai, trừ khi: đứng sau chị/anh/em/cô/thầy/bạn/bà/ông/chú/bác/dì/cậu
  ("chị mai" là tên người), hoặc viết đúng dạng "Mai" ở giữa câu (tên riêng). "Mai" đầu câu vẫn là ngày;
  "ngày mai", "sáng mai", "mai 9h" luôn là ngày.

## Bảng giờ

| Gõ | Kết quả |
|----|---------|
| giờ 1–5 không buổi | +12 (13:00–17:59) |
| giờ 0, 6–23 không buổi | giữ nguyên |
| `sáng` + 1–11 | giữ nguyên (`5h sáng` = 05:00); `12h sáng` không hợp lệ → giữ là chữ |
| `trưa` + 11–12 → giữ; + 1–2 → +12 | |
| `chiều`/`tối` + 1–11 → +12; + 12–23 → giữ | |
| `đêm` + 9–11 → +12; + 12 → 00:00 hôm sau; + 1–5 → giữ (`2h đêm` = 02:00) | |
| buổi đứng riêng | sáng 08:00, trưa 12:00, chiều 14:00, tối 20:00, đêm 22:00 |

## Giải nghĩa hạn (FR-028 + Clarifications)

1. Có date + time → ngày đó, giờ đó.
2. Chỉ date → hạn cả ngày.
3. Chỉ time → `viewDefaultDate` nếu có (kể cả giờ đã qua, `dueInPast = true`); nếu không: hôm nay nếu giờ chưa
   qua, nếu đã qua thì ngày mai.
4. Thứ X là hôm nay mà giờ đã qua → tuần sau.
5. recurrence không có date → ngày khớp quy tắc gần nhất từ hôm nay (áp quy tắc 3–4 cho giờ).
6. Không có date/time → `fields` không có hạn; giao diện dùng mặc định của danh sách đang xem.

## Tiêu đề

Bỏ các khoảng của cụm được hiểu (không bị huỷ), gộp khoảng trắng, bỏ dấu câu `, . ; : - –` ở hai đầu. Rỗng →
`titleMissing = true`, không tạo task.

## Ca kiểm thử bắt buộc

Toàn bộ bảng FR-030 và kịch bản US4 trong [spec.md](../spec.md) (now = 2026-11-05 10:00, xem "Tất cả") là một
phần của `quickParse.cases.ts`; tổng ≥ 400 ca theo nhóm ở research R12.
