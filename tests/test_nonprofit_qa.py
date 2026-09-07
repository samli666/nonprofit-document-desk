from nonprofit_qa import Document


def test_documents_keep_business_context():
    receipt = Document("r1", "Donor receipt for Ana: $75", "receipt")
    reminder = Document("v1", "Volunteer shift at 9 AM", "reminder")
    assert receipt.kind == "receipt"
    assert "$75" in receipt.text
    assert reminder.kind == "reminder"
