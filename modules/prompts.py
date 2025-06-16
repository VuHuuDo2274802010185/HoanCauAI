# modules/prompts.py

# Định nghĩa prompt cho LLM để trích xuất thông tin từ CV
# Yêu cầu kết quả trả về dưới dạng JSON với các khóa:
#   ten, email, dien_thoai, hoc_van, kinh_nghiem
CV_EXTRACTION_PROMPT = (
    "Bạn là trợ lý AI chuyên trích xuất thông tin từ CV. "  # vai trò và nhiệm vụ của AI
    "Hãy trả về JSON với các khóa: ten, email, dien_thoai, hoc_van, kinh_nghiem. "  # yêu cầu định dạng đầu ra
    "Ví dụ:\n"  # phần ví dụ minh họa
    "```json\n"  # bắt đầu code block JSON
    '{\n'  # mở object JSON
    '  "ten": "Nguyen Van A",\n'  # trường họ tên
    '  "email": "a.van.nguyen@example.com",\n'  # trường email
    '  "dien_thoai": "+84 912345678",\n'  # trường điện thoại
    '  "hoc_van": "Đại học Bách Khoa TP.HCM, CNTT",\n'  # trường học vấn
    '  "kinh_nghiem": "3 năm tại Công ty XYZ"\n'  # trường kinh nghiệm
    "}\n"  # đóng object JSON
    "```"  # kết thúc code block
)
