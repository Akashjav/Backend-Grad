"""Vector PDF certificate inspired by the supplied green-and-gold reference."""
from io import BytesIO
from math import cos, sin, radians
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


def render_certificate(certificate):
    output = BytesIO()
    width, height = landscape(A4)
    page = canvas.Canvas(output, pagesize=(width, height))
    page.setTitle("GradAlumni Certificate of Completion")
    page.setAuthor("GradAlumni")
    green, light, gold = "#28643D", "#619859", "#BC982D"
    data = certificate.snapshot

    def fill(value):
        page.setFillColor(colors.HexColor(value))

    def polygon(points, colour):
        fill(colour)
        path = page.beginPath()
        path.moveTo(*points[0])
        for point in points[1:]:
            path.lineTo(*point)
        path.close()
        page.drawPath(path, stroke=0, fill=1)

    def text(value, x, top, box_width, box_height, size=14, font="Times-Roman", colour="#242924", align=1):
        # Bounded text regions keep real names and long opportunity titles apart.
        for candidate in range(size, 5, -1):
            style = ParagraphStyle("certificate", fontName=font, fontSize=candidate,
                leading=candidate * 1.23, textColor=colors.HexColor(colour), alignment=align)
            paragraph = Paragraph(escape(str(value)), style)
            _, used = paragraph.wrap(box_width, box_height)
            if used <= box_height:
                break
        paragraph.drawOn(page, x, top - used)

    fill("#FFFFFF")
    page.rect(0, 0, width, height, fill=1, stroke=0)
    for x, y, radius, colour in [(width, 290, 190, "#F5F6F3"), (390, height, 115, "#F4F6F1"),
                                  (45, 10, 150, "#F5F6F3"), (520, 0, 85, "#F0F3E9")]:
        fill(colour)
        page.circle(x, y, radius, fill=1, stroke=0)
    page.setStrokeColor(colors.HexColor(gold))
    page.setLineWidth(1.3)
    page.rect(18, 18, width - 36, height - 36, fill=0)

    # Broad hanging ribbon, with darker edges and gold award medallion.
    fill("#204F2D")
    page.roundRect(61, 196, 144, 470, 66, stroke=0, fill=1)
    fill(green)
    page.roundRect(68, 200, 130, 470, 60, stroke=0, fill=1)
    fill(light)
    page.roundRect(75, 204, 116, 470, 54, stroke=0, fill=1)
    polygon([(101, 204), (71, 115), (102, 123), (122, 98), (142, 190)], green)
    polygon([(128, 192), (152, 98), (174, 124), (198, 119), (161, 214)], green)
    for radius, colour in [(58, "#F0D56F"), (52, gold), (46, "#F5D873"), (37, green)]:
        fill(colour)
        page.circle(133, 215, radius, fill=1, stroke=0)
    page.setStrokeColor(colors.HexColor(gold))
    page.setLineWidth(1.2)
    for side in [-1, 1]:
        for n in range(11):
            angle = radians(35 + n * 11)
            x = 133 + side * 66 * sin(angle)
            y = 215 + 66 * cos(angle)
            page.saveState()
            page.translate(x, y)
            page.rotate(side * (40 + n * 10))
            fill("#DFC252")
            page.ellipse(-3, -7, 3, 7, fill=1, stroke=0)
            page.restoreState()
    text("COMPLETED" if not certificate.revoked_at else "REVOKED", 98, 222, 70, 24,
         9, "Helvetica-Bold", "#FFFFFF")

    x, content_width = 247, width - 294
    text("GRADALUMNI", width - 186, height - 37, 145, 18, 15, "Helvetica-Bold", green, 2)
    text("ACADEMIA - INDUSTRY COLLABORATION", width - 266, height - 57, 225, 14, 6, "Helvetica", green, 2)
    text("CERTIFICATE", x, 505, content_width, 63, 46, "Times-Bold")
    kind = str(data.get("kind", "completion")).replace("_", " ")
    subtitle = {"internship": "OF INTERNSHIP", "faculty internship": "OF FACULTY INTERNSHIP"}.get(kind, "OF COMPLETION")
    polygon([(x + 12, 434), (x + content_width - 12, 434), (x + content_width - 24, 419),
             (x + content_width - 12, 404), (x + 12, 404), (x + 24, 419)], green)
    text(subtitle, x + 27, 430, content_width - 54, 25, 21, "Times-Bold", "#FFFFFF")
    text("This certificate is proudly presented to", x, 376, content_width, 30, 17, "Times-Italic")
    text(data["recipient"], x, 336, content_width, 65, 36, "Times-Italic", light)
    page.setStrokeColor(colors.HexColor("#D3D8CE"))
    page.setLineWidth(.7)
    page.line(x + 15, 267, x + content_width - 15, 267)
    text(f"For successfully completing the {kind} engagement", x, 249, content_width, 28, 16, "Times-Italic")
    text(data["title"], x + 6, 216, content_width - 12, 52, 21, "Times-Bold", green)
    text(f"Issued by {data['issuer']}", x, 157, content_width, 33, 14, "Times-Italic")

    # Real issuance metadata replaces the example's invented signatures.
    text(certificate.issued_at.strftime("%d %B %Y"), x, 110, 185, 25, 13, "Helvetica", green)
    text("DATE OF ISSUE (UTC)", x, 87, 185, 15, 7, "Helvetica")
    text("Evaluated completion", x + content_width - 200, 110, 200, 25, 13, "Helvetica", green)
    text("GRADALUMNI VERIFICATION RECORD", x + content_width - 200, 87, 200, 15, 7, "Helvetica")
    text(f"Verification code: {certificate.code}", x, 61, content_width, 15, 8, "Helvetica", green)
    text("Verify in GradAlumni > Certificates. Confirms engagement completion; not a professional licence.",
         x, 46, content_width, 14, 6, "Helvetica")
    if certificate.revoked_at:
        fill("#A72626")
        page.rect(x, 382, content_width, 19, fill=1, stroke=0)
        text("REVOKED - This certificate is no longer valid", x + 5, 399, content_width - 10, 16, 11, "Helvetica-Bold", "#FFFFFF")
    page.showPage()
    page.save()
    return output.getvalue()
