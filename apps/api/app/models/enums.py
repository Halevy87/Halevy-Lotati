import enum


class CaseStatus(str, enum.Enum):
    intake_pending = "intake_pending"
    intake_complete = "intake_complete"
    in_progress = "in_progress"
    needs_attention = "needs_attention"
    signing_scheduled = "signing_scheduled"
    signed = "signed"
    archived = "archived"


class DealType(str, enum.Enum):
    purchase = "purchase"
    sale = "sale"
    exchange = "exchange"


class PartyRole(str, enum.Enum):
    buyer = "buyer"
    seller = "seller"
    guarantor = "guarantor"
    spouse = "spouse"


class IdentityCheckStatus(str, enum.Enum):
    pending = "pending"
    clean = "clean"
    warning = "warning"
    red_flag = "red_flag"


class UserRole(str, enum.Enum):
    partner = "partner"
    lawyer = "lawyer"
    admin = "admin"


class DocumentType(str, enum.Enum):
    engagement_letter = "engagement_letter"
    kyc_form = "kyc_form"
    tax_calculation = "tax_calculation"
    client_id = "client_id"
    intake_pdf = "intake_pdf"
    taboo_consolidated = "taboo_consolidated"
    taboo_detailed = "taboo_detailed"
    condo_registration = "condo_registration"
    condo_bylaws = "condo_bylaws"
    condo_plan = "condo_plan"
    identity_check_report = "identity_check_report"
    govmap_report = "govmap_report"
    draft_contract = "draft_contract"
    reviewed_contract = "reviewed_contract"
    mortgage_approval = "mortgage_approval"
    spousal_consent = "spousal_consent"
    arnona_bill = "arnona_bill"
    other = "other"


class DocumentSource(str, enum.Enum):
    uploaded = "uploaded"
    generated = "generated"
    scraped = "scraped"


class ActivityType(str, enum.Enum):
    case_opened = "case_opened"
    step_started = "step_started"
    step_completed = "step_completed"
    step_flagged = "step_flagged"
    document_uploaded = "document_uploaded"
    document_generated = "document_generated"
    scraping_completed = "scraping_completed"
    scraping_failed = "scraping_failed"
    ai_analysis_completed = "ai_analysis_completed"
    client_message_sent = "client_message_sent"
    client_message_received = "client_message_received"
    red_flag_raised = "red_flag_raised"
    note_added = "note_added"
