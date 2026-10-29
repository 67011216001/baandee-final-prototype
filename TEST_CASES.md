## สรุปผลการทดสอบอัตโนมัติ (Automated Test Summary)

รันด้วยคำสั่ง `python tests/test_system.py` ผลรวม **5/5 tests passed**

| รหัส | ชื่อเทส | วัตถุประสงค์ | ข้อมูลนำเข้า | ผลที่คาดหวัง | ผลที่ได้จริง | สถานะ |
|---|---|---|---|---|---|---|
| TC-01 | Invalid Data Detection and Human Review | ตรวจว่าระบบจับข้อมูลที่ผิดปกติและส่งให้คนตรวจสอบได้ | ข้อมูลสินค้า สต็อก และ Supplier Lead Time | พบข้อมูลที่ต้องตรวจสอบอย่างน้อย 2 รายการ และทุกรายการมีเหตุผลกำกับ | ประมวลผล 82 SKUs พบ 5 รายการที่ต้องตรวจสอบ และมีเหตุผลครบ 5 รายการ | PASS |
| TC-02 | Supplier API Boundary Handling | ตรวจว่า API ตอบถูกต้องในกรณีขอบเขตต่าง ๆ | SKU ที่ถูกต้อง, SKU ที่ไม่มีในระบบ, ข้อมูล supplier ใช้งานไม่ได้ | ได้ HTTP 200, 404 และ 503 ตามลำดับ | 200=200, 404=404, 503=503 | PASS |
| TC-03 | Stock Risk Calculation Engine | ตรวจว่าการคำนวณความเสี่ยงสต็อกทำงานถูกต้อง | ข้อมูลที่ทำความสะอาดและ join แล้ว | คำนวณความเสี่ยงได้ พบ CRITICAL_RISK และ HUMAN_REVIEW_NEEDED | ประมวลผล 82 SKUs; CRITICAL_RISK=True; HUMAN_REVIEW_NEEDED=True | PASS |
| TC-04 | Reorder Request Create and Update | ตรวจการสร้างและอนุมัติคำขอสั่งซื้อ | SKU-0001, จำนวน 50 | สร้างเป็น Draft แล้วอัปเดตเป็น Approved ได้ | request_id=REQ-0001; created_as_Draft=True; update_success=True; approved=True | PASS |
| TC-05 | Soft Delete and Audit Trail | ตรวจว่าลบแบบ soft delete แล้วยังเก็บประวัติไว้ | Request ID: REQ-0001 | ซ่อนจากรายการปกติ แต่ยังเก็บในประวัติ และ is_deleted=True | delete_success=True; hidden_from_active=True; retained_in_history=True; is_deleted=True | PASS |

### คำอธิบายเพิ่มเติม
- **Soft delete** คือการทำเครื่องหมายว่าลบแล้ว (`is_deleted=True`) แทนการลบข้อมูลจริง เพื่อให้ตรวจย้อนหลังได้ (audit trail)
- **HUMAN_REVIEW_NEEDED** คือข้อมูลที่ระบบไม่มั่นใจ จึงส่งให้คนตัดสินใจ ไม่ตัดสินใจเอง
- **CRITICAL_RISK** คือสินค้าที่สต็อกเสี่ยงหมดก่อนของใหม่มาถึง
- เทสทั้งหมดรันด้วยข้อมูลชั่วคราว (sandbox) ไม่กระทบข้อมูลจริงของระบบ
