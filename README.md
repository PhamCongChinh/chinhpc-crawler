# Dantri Crawler

Thu thập tin bài từ [dantri.com.vn](https://dantri.com.vn) qua RSS feeds, lưu vào MongoDB.

## Kiến trúc

```
crawler/
├── main.py                      # Entry point
├── scheduler.py                 # Chạy định kỳ (APScheduler)
├── config.py                    # Đọc biến môi trường từ .env
├── requirements.txt
├── .env                         # Cấu hình (tạo từ .env.example)
├── crawlers/
│   └── dantri/
│       ├── feeds.py             # Danh sách 35 RSS feed URLs
│       ├── rss_fetcher.py       # Fetch RSS → metadata bài viết
│       └── article_parser.py   # Fetch HTML → nội dung đầy đủ
└── storage/
    └── mongodb.py               # Kết nối MongoDB, upsert, dedup
```

## Luồng xử lý

```
main.py
  └── for each RSS feed (35 feeds):
        ├── rss_fetcher.fetch_feed()   → list ArticleMetadata (tối đa 100 bài/feed)
        └── for each article:
              ├── mongodb.exists(url)?  → bỏ qua nếu đã có (dedup theo URL)
              ├── article_parser.parse(url)  → content, tags, images, categories
              └── mongodb.upsert(article)
```

Crawl delay **1 giây** giữa mỗi request (tuân thủ robots.txt của dantri).

## Cài đặt

```bash
pip install -r requirements.txt
cp .env.example .env
# Chỉnh sửa .env nếu cần
```

## Cấu hình (.env)

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `MONGODB_URI` | `mongodb://localhost:27017` | Connection string MongoDB |
| `MONGODB_DB` | `dantri_news` | Tên database |
| `CRAWL_DELAY_SECONDS` | `1` | Delay giữa các request (giây) |
| `SCHEDULE_INTERVAL_MINUTES` | `30` | Chu kỳ chạy lại khi dùng --schedule |

## Cách chạy

```bash
# Chạy 1 lần (toàn bộ 35 feeds)
python main.py

# Chạy định kỳ mỗi 30 phút (hoặc theo SCHEDULE_INTERVAL_MINUTES)
python main.py --schedule
```

> **Lưu ý:** Lần đầu crawl ~3500 bài × 1 giây delay ≈ 1–2 giờ. Các lần sau nhanh hơn vì bỏ qua bài đã có.

## MongoDB Schema

Collection: `dantri_news.articles`

| Field | Nguồn | Mô tả |
|-------|-------|-------|
| `_id` | URL bài viết | Unique key, dùng để dedup |
| `title` | RSS | Tiêu đề |
| `url` | RSS | URL đầy đủ |
| `slug` | URL | Phần slug trong URL |
| `article_id` | URL | Mã số bài (17 chữ số cuối URL) |
| `author` | RSS `dc:creator` | Tác giả |
| `published_at` | RSS `pubDate` | Ngày đăng (UTC) |
| `rss_category` | Feed slug | Chuyên mục RSS (vd: `cong-nghe`) |
| `categories` | HTML breadcrumb | Đường dẫn chuyên mục (vd: `['Công nghệ']`) |
| `summary` | RSS description | Tóm tắt ngắn |
| `thumbnail_url` | RSS description | Ảnh đại diện |
| `content` | HTML | Nội dung đầy đủ (text, cách nhau `\n\n`) |
| `tags` | HTML `/tim-kiem/` links | Từ khóa liên quan |
| `images` | HTML `<figure>` | List `{url, caption}` |
| `source` | hardcode | Luôn là `"dantri"` |
| `crawled_at` | runtime | Thời điểm crawl (UTC) |

Index: `published_at` (desc), `rss_category`

## Ghi chú kỹ thuật

- **Không có REST API công khai.** dantri dùng server-side rendering, WordPress REST API bị tắt.
- **RSS feeds** là cách duy nhất lấy dữ liệu có cấu trúc. Mỗi feed trả về 100 bài gần nhất.
- **CSS selectors:** Site dùng Tailwind utility classes với prefix `dt-` (không có class semantic). Content nằm trong `<article>` đầu tiên có class `dt-flex-col`. Tags là các `<a href="/tim-kiem/...">`.
- **Dedup** theo `_id` (URL), dùng `upsert` nên chạy lại an toàn.

## 35 RSS Feeds

| Slug | Chuyên mục |
|------|------------|
| `trang-chu` | Trang chủ |
| `thoi-su` | Thời sự |
| `the-gioi` | Thế giới |
| `kinh-doanh` | Kinh doanh |
| `the-thao` | Thể thao |
| `giao-duc` | Giáo dục |
| `suc-khoe` | Sức khỏe |
| `cong-nghe` | Công nghệ |
| `giai-tri` | Giải trí |
| `du-lich` | Du lịch |
| `phap-luat` | Pháp luật |
| `bat-dong-san` | Bất động sản |
| `doi-song` | Đời sống |
| `khoa-hoc` | Khoa học |
| ... | *(xem `crawlers/dantri/feeds.py` để đủ 35)* |
