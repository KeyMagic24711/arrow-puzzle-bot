# YÊU CẦU PHÁT TRIỂN PHẦN MỀM TỰ ĐỘNG GIẢI GAME MŨI TÊN – PHIÊN BẢN 2

> Tài liệu này dành cho lập trình viên hoặc AI phát triển phần mềm. Hãy đọc toàn bộ trước khi bắt đầu. Các giả định chưa chốt được liệt kê ở **Phụ lục A**. Nếu một giả định ảnh hưởng tới thiết kế, hãy hỏi lại trước khi triển khai.

---

## 1. Bối cảnh và lý do làm phiên bản mới

Đã có phiên bản 1 (v1) giải game mũi tên, thiết kế dạng module. Tuy nhiên v1 chia module quá nhỏ lẻ. Qua nhiều lần trao đổi và cập nhật, các tính năng bị gộp đi tách lại liên tục. Đến nay mã nguồn rối tới mức không thể cải tiến thêm.

Vì vậy cần xây dựng **phiên bản 2 (v2) mới hoàn toàn**, với các nguyên tắc sau:

- **v2 vẫn thiết kế dạng module**, nhưng chỉ gồm **5 module**: `Read Map`, `Solver`, `Stepper`, `Connection`, `UI`.
- **Được tham khảo v1 có chọn lọc.** v1 đã từng giải đúng bài toán này, nên những phần tốt, đã chạy ổn thì nên tận dụng. Đặc biệt là nhận diện mũi tên, xử lý vệt xám mép phải, chụp tốc độ cao và các thông số đã tinh chỉnh.
- **Không sao chép nguyên 100% v1**, để tránh mang lỗi cũ sang dự án mới.

---

## 2. Tổng quan quy trình một màn chơi

1. Kết nối điện thoại. Nếu máy đang ở ứng dụng khác thì **ép mở thẳng vào game**.
2. Mở một **màn chơi mới**.
3. Chụp **ảnh đầu tiên** (ở vị trí giữa, mặc định khi mở màn) để xác định loại bản đồ:
   - **Bản đồ nhỏ**: toàn bộ mũi tên nằm gọn trong một khung hình. Giải luôn trên ảnh này.
   - **Bản đồ lớn**: mũi tên tràn ra ngoài, khung hình chỉ hiển thị được một phần. Cần chụp nhiều ảnh rồi ghép thành bản đồ hoàn chỉnh (xem mục 3).
4. Nhận diện mũi tên trên bản đồ hoàn chỉnh.
5. Chia khu, chọn thứ tự khu và giải (xem mục 4 và 5).
6. Hết màn thì mở màn mới và lặp lại.

---

## 3. Module READ MAP – Chụp, ghép bản đồ và nhận diện

> **Đây là một trong hai phần quan trọng nhất.** Ghép bản đồ phải thật chuẩn thì giải mới chuẩn được.

### 3.1. Ảnh đầu tiên

Với bản đồ lớn, ảnh đầu tiên chụp ở giữa **chỉ dùng để phân loại bản đồ, không dùng làm ảnh ghép**. Không ghép bắt đầu từ giữa.

### 3.2. Đưa khung hình về góc trên cùng bên trái

1. Vuốt **thật nhanh, thật mạnh, thật dài** để đẩy khung hình lên trên cùng.
2. Vuốt **thật nhanh, thật mạnh, thật dài** để đẩy khung hình sang hết bên trái.

Đây là gợi ý. Có thể dùng cách hợp lý hơn nếu có.

### 3.3. Chụp theo hình zíc zắc

Bắt đầu từ góc trên trái:

1. Kéo sang phải từng khung, chụp từng khung, đến khi kịch mép phải.
2. Di chuyển xuống dưới một hàng.
3. Kéo sang trái từng khung đến khi kịch mép trái.
4. Lại xuống dưới, lại sang phải… cho đến khi phủ hết bản đồ.

Mỗi lần di chuyển **không sang hẳn khung mới**. Giữ lại khoảng **15–20% khung hình cũ** làm vùng chồng lấn, để thuật toán ghép có điểm nhận diện và ghép được.

### 3.4. Lỗi đã biết khi ghép

Mép phải màn hình luôn có **hai nút ảo**, tạo ra **vệt màu xám**. Cần loại bỏ hoặc che vùng này trước khi ghép. v1 đã từng xử lý lỗi này, nên rà soát lại mã cũ để tham khảo.

### 3.5. Tốc độ chụp và cơ chế chụp – ghép song song

- **Chụp:** dùng lại hướng của v1 (dự án GitHub quay và chụp màn hình liên tục) để chụp thật nhanh. Xem lại v1 để tham khảo.
- **Ghép song song với chụp.** Không làm kiểu chụp một ảnh, ghép xong rồi mới chụp tiếp, vì chờ rất lâu. Việc chụp chạy liên tục, việc ghép chạy song song:
  - Ảnh chụp **đánh số thứ tự 1, 2, 3, 4…** để ghép đúng thứ tự, không nhầm.
  - **Ảnh cuối cùng đặt tên có đánh dấu riêng** để bộ ghép biết đã hết ảnh.
  - Nếu ghép nhanh hơn chụp, bộ ghép **chờ file tiếp theo** xuất hiện rồi ghép tiếp.
  - Nếu chụp nhanh hơn ghép, ảnh xếp hàng chờ. Phương án chụp hết rồi mới ghép cũng chấp nhận được.

### 3.6. Nhận diện mũi tên

Logic nhận diện **tham khảo v1**. Các đặc điểm hình ảnh cần lưu ý:

| Đối tượng | Đặc điểm | Cách xử lý |
|---|---|---|
| Mũi tên thường | Màu đen | Giải bình thường |
| Mũi tên gợi ý | Màu hơi xanh | Đây chỉ là gợi ý của game. Bỏ qua màu, coi như mũi tên thường |
| Mũi tên thưởng | Óng ánh bảy sắc cầu vồng, nhạt, giống mặt đĩa CD | Bấm vào sẽ tự giải kèm một số mũi tên khác (xem 5.5) |
| Chấm tròn xám mờ | Xuất hiện ở màn đang chơi dở, tại chỗ mũi tên đã đi | **Chỉ là điểm định vị lưới, KHÔNG phải mũi tên.** Không nhận nhầm, tránh bị kẹt |

Màn mở mới hoàn toàn thì vùng không có mũi tên để **trắng trơn**, không có chấm.

---

## 4. Module SOLVER – Chia khu và lập thứ tự giải

> **Đây là phần quan trọng thứ hai.** Thước đo có hai tiêu chí: **chính xác** và **nhanh**. **Ưu tiên chính xác trước**, khi đã ổn định mới cải thiện dần tốc độ.

### 4.1. Chia khu

Màn hình chỉ hiển thị một phần bản đồ, nên phải chia bản đồ lớn thành các khu, mỗi khu vừa một khung hình.

- Số khu **càng ít càng tốt**, nhưng phải đủ phủ hết bản đồ.
- Các khu **chồng lấn nhau một chút**, để tránh mũi tên kẹt ở mép giữa hai khu mà không xử lý được. Không chồng lấn quá nhiều.
- Mục đích chia khu là xác định **thứ tự di chuyển** giữa các khu.

### 4.2. Chọn thứ tự khu

- Giải trước khu có **nhiều mũi tên giải được nhất** tại thời điểm đó. Ví dụ khu 3 có nhiều mũi tên giải được ngay nhất thì giải khu 3 trước.
- Giải xong một khu, tính lại để chọn khu có nhiều mũi tên giải được nhất tiếp theo, vì sau mỗi khu sẽ có thêm mũi tên mới thông đường.

### 4.3. Mũi tên nằm không trọn trong khu

Nếu đã xác định một mũi tên bấm được, thì **vẫn bấm** dù trong khu chỉ thấy phần đầu, phần đuôi hoặc phần thân của nó.

### 4.4. Khái niệm "lớp" mũi tên

Một **lớp** là tập các mũi tên **không bị mũi tên nào chặn đường thoát**, nên có thể giải độc lập cùng lúc. Đường thoát của chúng cắt nhau thế nào không quan trọng. Điều kiện chỉ là không có mũi tên nào phải chờ mũi tên khác trong cùng lớp giải xong.

---

## 5. Module STEPPER – Thực thi bấm, theo dõi tim và xử lý lỗi

### 5.1. Quy luật tim (mạng) của game

- Mỗi màn có **3 tim**, tương ứng 3 lần bấm sai.
- Bấm sai **một mũi tên A**, rồi bấm sai lại chính A nhiều lần: **không bị trừ thêm tim**.
- Bấm sai **sang một mũi tên khác**: mất thêm một tim.

### 5.2. Cách 1 – Giải nhanh (mặc định)

**Điều kiện:** thứ tự giải các mũi tên trong khu đã được tính đúng hoàn toàn.

- Bấm liên tục theo đợt, mỗi đợt **5–10 mũi tên**, tùy khu nhiều hay ít mũi tên giải được.
- Khoảng cách giữa hai lần bấm: **ngẫu nhiên trong khoảng 150–200 ms** (ví dụ 162, 187, 155…).
- Sau mỗi đợt, **chụp lại màn hình** để xác nhận đợt đó đã đúng, rồi mới bấm đợt tiếp theo.

### 5.3. Cơ chế theo dõi tim và chuyển sang giải chậm

- Phải có **cơ chế theo dõi tim liên tục**.
- Vì bấm liên tục nên có thể sai hai mũi tên ngay lập tức. Hễ phát hiện **mất tim (dù 1 hay 2 tim)**:
  1. **Cưỡng ép dừng bấm ngay.**
  2. Chụp vài ảnh khu vực xung quanh để xác định nguyên nhân.
  3. **Ghi log lỗi**: bấm sai mũi tên nào, ảnh trước và sau. Cơ chế lưu lỗi này phải có **ngay từ đầu**.
  4. Nếu do bỏ sót, bấm lại đúng mũi tên đó.
  5. **Chuyển sang Cách 2 – Giải chậm.**

### 5.4. Cách 2 – Giải chậm (giải theo lớp)

1. Xác định lớp hiện tại (theo 4.4). Ví dụ lớp 1 có 3 mũi tên.
2. Bấm liên tục các mũi tên trong lớp, cách nhau ngẫu nhiên 150–200 ms.
3. Chụp xác nhận, xác định lớp kế tiếp, tức các mũi tên vừa được thông đường.
4. Lặp lại. Mỗi lớp có bao nhiêu mũi tên thì bấm bấy nhiêu. Ví dụ lớp 2 có 2 mũi, lớp 3 có 1 mũi, lớp 4 có 2 mũi.

### 5.5. Mũi tên thưởng

Sau khi bấm mũi tên thưởng, **chụp nhanh vùng xung quanh** để cập nhật những mũi tên đã tự được giải kèm.

Bấm lại một mũi tên đã giải thì không gây hại, nhưng mất thời gian. Chụp cập nhật giúp tiết kiệm thời gian bấm.

### 5.6. Kiểm tra trước khi rời khu

Trước khi rời một khu, **chụp lại một lần cuối** để kiểm tra mọi mũi tên đã tính cho khu này đã đi hết chưa.

- Đã hết: ghi nhận và chuyển sang khu tiếp theo.
- Còn sót: bấm nốt những mũi tên cần thiết nhất cho đến khi sạch, rồi mới chuyển khu.

---

## 6. Module CONNECTION – Kết nối và xử lý gián đoạn

- Phát hiện điện thoại, kết nối và ép mở thẳng vào game.
- **Xử lý khi bị gián đoạn**, ví dụ game bị thoát ra, người dùng cầm máy thao tác, hoặc rút cáp rồi cắm lại. Khi kết nối lại thì xác định lại màn hiện tại:

| Tình huống | Xử lý |
|---|---|
| Đúng màn cũ, không thay đổi gì | Chơi tiếp |
| Đúng màn cũ nhưng khung hình bị xê dịch | Chụp và định vị lại khung hình, rồi chơi tiếp |
| Đúng màn cũ nhưng người dùng đã bấm làm mất vài mũi tên | Kiểm tra vài vị trí, cập nhật trạng thái mũi tên, rồi chơi tiếp |
| Là màn khác hoàn toàn | Chụp lại bản đồ từ đầu, **reset đồng hồ thứ hai** (đồng hồ màn) |

---

## 7. Module UI – Giao diện

### 7.1. Nút điều khiển

- **Bắt đầu**: chạy phần mềm. Sau khi bấm Dừng, nút này đổi thành **Tiếp tục**.
- **Dừng**: dừng **toàn bộ** thao tác của phần mềm, không chạy, không giải gì. Không cần thêm nút Tạm dừng riêng.
- **Reset**: xóa toàn bộ thông tin giải hiện tại, coi như vừa tắt bật lại phần mềm, rồi giải lại từ đầu.
- **Lấy lại bản đồ**: nút nhỏ đặt ở mục ghép bản đồ. Khi bấm, phần mềm cưỡng ép quá trình giải hiện tại, tự chụp và ghép lại bản đồ như khi mới mở màn, tự lập phương án giải mới và tự chơi tiếp.

### 7.2. Hai đồng hồ đếm thời gian

- **Đồng hồ 1 – Tổng thời gian chạy:** đếm xuyên suốt từ lúc bấm Bắt đầu, kể cả giai đoạn kiểm tra điện thoại, khởi tạo, và những lúc không bấm. Chỉ dừng khi bấm Dừng.
- **Đồng hồ 2 – Thời gian giải màn:** bắt đầu khi vào màn chơi. Đếm cả thời gian chụp ảnh đầu, phân loại bản đồ, ghép bản đồ và tính toán. Dừng khi kết thúc màn. Mục đích là biết mỗi màn giải hết bao lâu.

### 7.3. Hiệu năng giao diện

Chuyển giữa các tab **không giật lag**. Các tab được tải sẵn, không tải lại mỗi lần chuyển.

### 7.4. Menu module và cập nhật

- **Giữ cơ chế ép cập nhật**, hiện thông báo như v1.
- Mục menu module vẫn có các chức năng: chọn phiên bản, tự cài đặt, hiển thị trạng thái, hiển thị phiên bản module đang dùng.

### 7.5. Bỏ kênh "nhờ bot trợ giúp"

**Không** làm kênh để bot can thiệp hoặc người dùng xin bot trợ giúp trong phần mềm, vì chỉ mất thời gian mà không giải quyết được vấn đề. Thay vào đó dùng cơ chế ghi log ở mục 8.

---

## 8. Cơ chế ghi nhận thông số và log (bắt buộc có từ đầu)

- Ghi lại **đầy đủ thông số** của mọi lỗi và mọi diễn biến quan trọng, gồm cả thông số định kỳ, không chỉ khi có lỗi. Ví dụ: thời gian từng bước, kết quả ghép, mũi tên nhận diện được, thứ tự bấm, ảnh trước và sau khi sai, số tim, lần chuyển cách giải.
- Lưu vào **một thư mục cố định trên máy local**. Khi cần cập nhật, người dùng gửi đường dẫn hoặc file log cho lập trình viên/AI, hoặc cho phép truy cập trực tiếp thư mục đó.
- **Mục tiêu:** chỉ cần đọc log là tự suy ra được lỗi gì và cần điều chỉnh gì ở lần cải tiến tiếp theo, không phải hỏi lại.

---

## 9. Nguyên tắc ưu tiên

1. Ghép bản đồ chuẩn và giải đúng là hai phần cần đầu tư suy nghĩ kỹ nhất.
2. **Chính xác trước, nhanh sau.**
3. Tham khảo thông số và mã của v1 ở mức hợp lý, không lặp lại lỗi cũ.
4. Log đầy đủ ngay từ phiên bản đầu tiên.

---

## Phụ lục A – Các giả định chưa chốt

Tài liệu đang áp dụng các giả định dưới đây. Người đặt yêu cầu sẽ xác nhận sau.

1. **Phân công chức năng cho 5 module** trong tài liệu này được sắp xếp theo nội dung trao đổi. Tên và chức năng các module đã được chốt ở lần trao đổi trước, nên cần đối chiếu lại, đặc biệt với `Stepper` và `Connection`.
2. **Khoảng cách bấm:** cả hai cách giải dùng 150–200 ms. Có lúc trao đổi nhắc 100–150 ms cho cách giải chậm.
3. **Khi mất tim:** đang áp dụng mất bất kỳ tim nào là dừng, chẩn đoán, ghi log rồi chuyển sang giải chậm.
4. **Giải chậm:** có bước chụp xác nhận sau mỗi lớp để xác định lớp kế tiếp.
5. **Truy cập log:** cách cụ thể (gửi link, đồng bộ đám mây hay truy cập trực tiếp thư mục local) chưa chốt.
6. **Nút Reset:** chưa chốt Reset có đặt lại cả hai đồng hồ hay chỉ đồng hồ 2.
