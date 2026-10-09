"""Build docs/North_Star_AWS_Services.pdf: one page listing every Amazon tool and service North Star uses.

    pip install reportlab
    python scripts/build_services_pdf.py
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "North_Star_AWS_Services.pdf"

MIDNIGHT, PANEL, OCEAN = colors.HexColor("#0C1626"), colors.HexColor("#15243A"), colors.HexColor("#2F6C8A")
AURORA, SILVER, ICE = colors.HexColor("#9DE5F4"), colors.HexColor("#B6CFEB"), colors.HexColor("#F3F7FC")
INK, MUTED, RULE = colors.HexColor("#1B2738"), colors.HexColor("#5B6B80"), colors.HexColor("#D5E0EE")

# (group, [(name, what it does in North Star)])
GROUPS = [
    ("AI and agents", [
        ("Amazon Bedrock", "Hosts and runs the models; every agent call goes through it"),
        ("Amazon Nova 2 Lite", "The model behind the coordinator and all three specialists"),
        ("Amazon Bedrock Knowledge Bases", "Retrieves policy text so answers cite a document and section"),
        ("Amazon Titan Text Embeddings V2", "Turns the policy documents into vectors for search"),
        ("Strands Agents", "Open-source agent framework from AWS; the agents and their tools are built with it"),
    ]),
    ("Data and storage", [
        ("Amazon DynamoDB", "One table for employee records and confirmed requests"),
        ("Amazon S3", "Stores the six policy documents"),
        ("Amazon S3 Vectors", "Stores the vectors the Knowledge Base searches"),
    ]),
    ("Hosting", [
        ("Amazon EC2", "The t3.small server that runs the app"),
        ("Amazon Linux 2023", "The server's operating system image"),
        ("Amazon EBS", "The server's 12 GB disk"),
        ("Elastic IP", "A fixed public address, so the QR code survives restarts"),
        ("Amazon VPC security group", "Opens port 80 only; no SSH"),
    ]),
    ("Operations, reused from our EC2 Scheduler project", [
        ("Amazon EventBridge Scheduler", "Triggers the 8:00 AM start and 6:00 PM stop"),
        ("AWS Lambda", "The functions that start and stop the server"),
        ("Amazon SNS", "Emails us when the server starts or stops"),
        ("Amazon SQS", "Dead-letter queue that catches a failed schedule run"),
        ("Amazon CloudWatch Logs", "Logs from the scheduler's functions"),
        ("AWS CloudFormation and AWS SAM", "Define the scheduler as code"),
        ("AWS Budgets", "A $5 monthly budget with alerts"),
    ]),
    ("Security and access", [
        ("AWS IAM", "Least-privilege roles for the server and the Knowledge Base"),
        ("AWS STS", "Short-lived credentials; no keys stored in code or on the server"),
        ("AWS Systems Manager", "Looks up the current server image; Session Manager gives shell access without SSH"),
    ]),
    ("Developer tools", [
        ("AWS CLI v2", "Sign-in with aws login, and setup from the terminal on Mac and Windows"),
        ("AWS SDK for Python (Boto3)", "How the app and scripts call AWS"),
        ("AWS Management Console", "Building and inspecting resources by hand"),
        ("AWS CloudShell", "Browser terminal used for early checks"),
    ]),
]

PAGE_W, PAGE_H = letter
MARGIN = 0.6 * inch
STAR = [(0, 1), (0.16, 0.16), (1, 0), (0.16, -0.16), (0, -1), (-0.16, -0.16), (-1, 0), (-0.16, 0.16)]


def star(c, x, y, size, fill):
    path = c.beginPath()
    path.moveTo(x + STAR[0][0] * size, y + STAR[0][1] * size)
    for px, py in STAR[1:]:
        path.lineTo(x + px * size, y + py * size)
    path.close()
    c.setFillColor(fill)
    c.drawPath(path, stroke=0, fill=1)


def main() -> None:
    name_style = ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=8.7, leading=10.6, textColor=INK)
    use_style = ParagraphStyle("use", fontName="Helvetica", fontSize=8.7, leading=10.6, textColor=INK)
    group_style = ParagraphStyle("group", fontName="Helvetica-Bold", fontSize=8.4, leading=10.5, textColor=colors.white)

    rows, style = [], [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 3.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.6),
        ("BOX", (0, 0), (-1, -1), 0.6, RULE),
    ]
    for group, items in GROUPS:
        style += [("SPAN", (0, len(rows)), (-1, len(rows))), ("BACKGROUND", (0, len(rows)), (-1, len(rows)), OCEAN)]
        rows.append([Paragraph(group.upper(), group_style), ""])
        for index, (name, use) in enumerate(items):
            if index % 2:
                style.append(("BACKGROUND", (0, len(rows)), (-1, len(rows)), ICE))
            style.append(("LINEBELOW", (0, len(rows)), (-1, len(rows)), 0.4, RULE))
            rows.append([Paragraph(name, name_style), Paragraph(use, use_style)])

    width = PAGE_W - 2 * MARGIN
    table = Table(rows, colWidths=[width * 0.33, width * 0.67])
    table.setStyle(TableStyle(style))

    c = canvas.Canvas(str(OUTPUT), pagesize=letter)
    c.setTitle("North Star: Amazon tools and services")
    c.setAuthor("David Dunmeyer and Biswa")

    band = 1.18 * inch
    c.setFillColor(MIDNIGHT)
    c.rect(0, PAGE_H - band, PAGE_W, band, stroke=0, fill=1)
    c.setStrokeColor(colors.HexColor("#3A5677"))
    c.setFillColor(PANEL)
    c.roundRect(MARGIN, PAGE_H - band + 22, 42, 42, 8, stroke=1, fill=1)
    star(c, MARGIN + 21, PAGE_H - band + 43, 14, AURORA)
    star(c, MARGIN + 21, PAGE_H - band + 43, 5.5, colors.white)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 19)
    c.drawString(MARGIN + 56, PAGE_H - band + 47, "Amazon tools and services in North Star")
    c.setFillColor(SILVER)
    c.setFont("Helvetica", 10)
    count = sum(len(items) for _, items in GROUPS)
    c.drawString(MARGIN + 56, PAGE_H - band + 29,
                 f"{count} tools and services across {len(GROUPS)} areas  |  Agentic AI, IT Expert System  |  David Dunmeyer and Biswa")

    _, height = table.wrap(width, PAGE_H)
    top = PAGE_H - band - 0.22 * inch
    if height > top - 0.62 * inch:
        raise SystemExit(f"The table needs {height:.0f} points and only {top - 0.62 * inch:.0f} fit on one page.")
    table.drawOn(c, MARGIN, top - height)

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.8)
    c.drawString(MARGIN, 0.4 * inch, "North Star: an employee assistant built with AI agents on AWS. All records in it are fictional. "
                                     "Region: us-east-1 (N. Virginia).")
    c.showPage()
    c.save()
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size // 1024} KB), {count} entries, one page")


if __name__ == "__main__":
    main()
