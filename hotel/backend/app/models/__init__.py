from app.models.user import User, RefreshToken
from app.models.audit import AuditLog
from app.models.front_office import RoomType, Room, Guest, Reservation, Stay, Trace, RoomStatus, ReservationStatus, ReservationSource, TracePriority, TraceStatus
from app.models.finance import Folio, FolioItem, Payment, NightAuditRun, FolioStatus, FolioItemType, PaymentMethod, PaymentStatus
from app.models.housekeeping import HousekeepingTask, LostFound, MinibarItem
# Faz 2 modelleri (Channel Manager, Muhasebe, CRM, Loyalty, Chat, Raporlama)
from app.models.channel import Channel
from app.models.channel_mapping import ChannelMapping
from app.models.channel_sync_log import ChannelSyncLog
from app.models.overbooking_rule import OverbookingRule
from app.models.rate_recommendation import RateRecommendation
from app.models.occupancy_forecast import OccupancyForecast
from app.models.chart_of_accounts import ChartOfAccount
from app.models.ledger_entry import LedgerEntry
from app.models.einvoice import EInvoice
from app.models.budget import Budget
from app.models.loyalty_account import LoyaltyAccount
from app.models.loyalty_transaction import LoyaltyTransaction
from app.models.complaint import Complaint
from app.models.feedback import Feedback
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.custom_report import CustomReport
from app.models.ai_invocation import AIInvocation
# Faz 3 modelleri (Groups, Events, Maintenance, ve diğer modüller)
from app.models.groups import Venue, Group, RoomBlock, Event, EventResource, GroupRoomingList
from app.models.maintenance import Asset, WorkOrder, PreventiveMaintenance, MaintenanceLog
# Faz 3 - HR & Shift modelleri
from app.models.hr import Employee, Shift, ShiftAssignment, Attendance, LeaveRequest
# Faz 3 - GDS Integration modelleri
from app.models.gds import GDSChannel, GDSReservation, GDSRateMapping, GDSSyncLog
# Faz 3 - IoT / Smart Room modelleri
from app.models.iot import IoTDevice, IoTDeviceLog, IoTScenario, IoTEnergyReading, IoTAlert
# Faz 4 - Computer Vision modelleri
from app.models.cv import CVModel, RoomInspection, InspectionDefect, InventorySnapshot
# Faz 4 - Voice Control modelleri
from app.models.voice import VoiceIntegration, VoiceCommand, VoiceSession, VoiceInteraction, VoiceIntentsMapping
# Faz 4 - Chain / Multi-Property modelleri
from app.models.chain import Chain, Property, PropertySyncLog, ConsolidatedReport, PropertyUser
# Faz 4 - Mobile Check-in modelleri
from app.models.mobile_checkin import OCRDocumentScan, EGMSubmission, CheckinSession, FacialRecognitionScan, NFCRoomKey
# Faz 4 - Blockchain Identity modelleri
from app.models.blockchain_identity import BlockchainIdentity, VerifiableCredential, IdentityVerificationProof, BlockchainSyncEvent, GuestConsentLog
