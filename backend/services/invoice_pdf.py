from fpdf import FPDF
from io import BytesIO
from datetime import datetime
import os
from loguru import logger

# Try to load a Unicode TTF font that supports Devanagari (Hindi) text.
# Falls back to Helvetica (built-in) if no font file is available — Hindi text
# may not render correctly in that case but the PDF will still generate.
_FONT_LOADED = False
_FONT_REGULAR = None
_FONT_BOLD = None

def _load_unicode_font():
    """Attempt to load a Unicode TTF font for Devanagari support."""
    global _FONT_LOADED, _FONT_REGULAR, _FONT_BOLD
    if _FONT_LOADED:
        return
    _FONT_LOADED = True
    # Search common system font locations for a Devanagari-capable TTF
    candidates = []
    if os.name == "nt":
        win_dir = os.environ.get("WINDIR", r"C:\Windows")
        candidates = [
            os.path.join(win_dir, "Fonts", "Nirmala.ttf"),
            os.path.join(win_dir, "Fonts", "NirmalaB.ttf"),
            os.path.join(win_dir, "Fonts", "Mangal.ttf"),
            os.path.join(win_dir, "Fonts", "Mangalb.ttf"),
            os.path.join(win_dir, "Fonts", "arial.ttf"),
            os.path.join(win_dir, "Fonts", "arialbd.ttf"),
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            if "b" in os.path.basename(path).lower() or "bold" in path.lower():
                if not _FONT_BOLD:
                    _FONT_BOLD = path
            else:
                if not _FONT_REGULAR:
                    _FONT_REGULAR = path
    if _FONT_REGULAR and _FONT_BOLD:
        logger.info(f"Loaded Unicode fonts: {_FONT_REGULAR}, {_FONT_BOLD}")
    elif _FONT_REGULAR:
        _FONT_BOLD = _FONT_REGULAR
        logger.info(f"Loaded Unicode font (regular only): {_FONT_REGULAR}")


class InvoicePDF(FPDF):
    def __init__(self, business_name="", business_address="", business_phone=""):
        super().__init__()
        self.business_name = business_name
        self.business_address = business_address
        self.business_phone = business_phone
        _load_unicode_font()

    def _set_font(self, style="", size=10):
        """Set font — uses Unicode TTF if loaded, else Helvetica."""
        if _FONT_REGULAR:
            font_path = _FONT_BOLD if "B" in style else _FONT_REGULAR
            family = os.path.splitext(os.path.basename(font_path))[0]
            try:
                self.add_font(family, style=style, fname=font_path)
                self.set_font(family, style=style, size=size)
                return
            except Exception:
                pass
        self.set_font("Helvetica", style=style, size=size)

    def header(self):
        self._set_font("B", 18)
        self.set_text_color(30, 30, 30)
        self.cell(0, 10, self.business_name or "Business", new_x="LMARGIN", new_y="NEXT", align="L")

        if self.business_address:
            self._set_font("", 9)
            self.set_text_color(120, 120, 120)
            self.cell(0, 5, self.business_address, new_x="LMARGIN", new_y="NEXT", align="L")
        if self.business_phone:
            self._set_font("", 9)
            self.set_text_color(120, 120, 120)
            self.cell(0, 5, self.business_phone, new_x="LMARGIN", new_y="NEXT", align="L")

        self.ln(5)
        self.set_draw_color(245, 175, 50)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def footer(self):
        self.set_y(-20)
        self._set_font("I", 8)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}", align="C")


def generate_invoice_pdf(
    invoice_number: str,
    order: dict,
    items: list[dict] = None,
    business_name: str = "Business",
    business_address: str = "",
    business_phone: str = "",
    gst_number: str = "",
    notes: str = "",
) -> bytes:
    pdf = InvoicePDF(business_name, business_address, business_phone)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=25)

    # Invoice title + number
    pdf._set_font( "B", 12)
    pdf.set_text_color(245, 150, 50)
    pdf.cell(0, 8, "INVOICE", new_x="LMARGIN", new_y="NEXT", align="R")

    pdf._set_font( "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, f"Invoice #: {invoice_number}", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.cell(0, 5, f"Date: {datetime.now().strftime('%d %b %Y')}", new_x="LMARGIN", new_y="NEXT", align="R")

    if gst_number:
        pdf.cell(0, 5, f"GSTIN: {gst_number}", new_x="LMARGIN", new_y="NEXT", align="R")

    pdf.ln(8)

    # Bill To
    pdf._set_font( "B", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, "Bill To:", new_x="LMARGIN", new_y="NEXT")

    pdf._set_font( "", 10)
    pdf.cell(0, 5, order.get("customer_name", "Customer"), new_x="LMARGIN", new_y="NEXT")
    if order.get("customer_phone"):
        pdf.cell(0, 5, f"Phone: {order['customer_phone']}", new_x="LMARGIN", new_y="NEXT")
    if order.get("delivery_address"):
        pdf.cell(0, 5, f"Address: {order['delivery_address']}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # Table header
    pdf.set_fill_color(245, 175, 50)
    pdf.set_text_color(255, 255, 255)
    pdf._set_font( "B", 9)
    pdf.cell(10, 8, "#", border=1, fill=True, align="C")
    pdf.cell(80, 8, "Item", border=1, fill=True, align="L")
    pdf.cell(25, 8, "Qty", border=1, fill=True, align="C")
    pdf.cell(35, 8, "Unit Price", border=1, fill=True, align="R")
    pdf.cell(40, 8, "Amount", border=1, fill=True, align="R")

    pdf.ln()

    # Table rows
    pdf.set_text_color(30, 30, 30)
    pdf._set_font( "", 9)

    line_items = items or [{"name": order.get("product_name", "Item"), "qty": order.get("quantity", 1), "price": order.get("unit_price", order.get("total_price", 0))}]

    for i, item in enumerate(line_items, 1):
        qty = item.get("qty", 1)
        price = item.get("price", 0)
        amount = qty * price

        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(252, 249, 240)

        pdf.cell(10, 7, str(i), border=1, fill=fill, align="C")
        pdf.cell(80, 7, str(item.get("name", "Item"))[:40], border=1, fill=fill, align="L")
        pdf.cell(25, 7, str(qty), border=1, fill=fill, align="C")
        pdf.cell(35, 7, f"Rs.{price:,.2f}", border=1, fill=fill, align="R")
        pdf.cell(40, 7, f"Rs.{amount:,.2f}", border=1, fill=fill, align="R")
        pdf.ln()

    # Totals
    pdf.ln(3)
    subtotal = sum(item.get("qty", 1) * item.get("price", 0) for item in line_items)
    discount = order.get("discount_amount", 0)
    delivery_fee = order.get("delivery_fee", 0)
    total = subtotal - discount + delivery_fee

    pdf._set_font( "", 10)
    pdf.cell(150, 7, "Subtotal:", align="R")
    pdf.cell(40, 7, f"Rs.{subtotal:,.2f}", align="R")
    pdf.ln()

    if discount > 0:
        pdf.set_text_color(180, 50, 50)
        pdf.cell(150, 7, f"Discount ({order.get('coupon_code', '')}):", align="R")
        pdf.cell(40, 7, f"-Rs.{discount:,.2f}", align="R")
        pdf.ln()
        pdf.set_text_color(30, 30, 30)

    if delivery_fee > 0:
        pdf.cell(150, 7, "Delivery Fee:", align="R")
        pdf.cell(40, 7, f"Rs.{delivery_fee:,.2f}", align="R")
        pdf.ln()

    # Total line
    pdf.set_draw_color(30, 30, 30)
    pdf.set_line_width(0.3)
    pdf.line(150, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(2)

    pdf._set_font( "B", 12)
    pdf.cell(150, 8, "Total:", align="R")
    pdf.cell(40, 8, f"Rs.{total:,.2f}", align="R")
    pdf.ln()

    # Payment status
    pdf.ln(5)
    status = order.get("status", "pending")
    status_colors = {"pending": (200, 150, 0), "confirmed": (0, 150, 80), "delivered": (0, 150, 80), "cancelled": (200, 50, 50)}
    r, g, b = status_colors.get(status, (120, 120, 120))
    pdf._set_font( "B", 10)
    pdf.set_text_color(r, g, b)
    pdf.cell(0, 7, f"Status: {status.upper()}", new_x="LMARGIN", new_y="NEXT", align="L")

    # Delivery type
    if order.get("delivery_type"):
        pdf._set_font( "", 9)
        pdf.set_text_color(80, 80, 80)
        dtype = "Home Delivery" if order["delivery_type"] == "delivery" else "Store Pickup"
        pdf.cell(0, 5, f"Delivery: {dtype}", new_x="LMARGIN", new_y="NEXT")

    # Notes
    if notes:
        pdf.ln(5)
        pdf._set_font( "I", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.multi_cell(0, 5, f"Note: {notes}")

    # Thank you
    pdf.ln(10)
    pdf._set_font( "I", 10)
    pdf.set_text_color(245, 150, 50)
    pdf.cell(0, 7, "Thank you for your business!", align="C")

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output.read()
