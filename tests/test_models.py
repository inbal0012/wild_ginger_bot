import pytest
from unittest.mock import Mock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from telegram_bot.models.registration import (
    RegistrationStatus, Status, RegistrationStage, 
    CreateRegistrationDTO, RegistrationData, PartnerInfo
)
from telegram_bot.models.user import CreateUserFromTelegramDTO
from telegram_bot.models.event import EventDTO
from telegram_bot.models.TelegramPollFields import TelegramPollFields, TelegramPollData
from telegram_bot.models.form_flow import (
    QuestionDefinition, QuestionType, QuestionOption, 
    Text, ValidationRule, ValidationRuleType
)


class TestRegistrationModels:
    """Test suite for registration-related models"""
    
    def test_registration_status_enum(self):
        """Test RegistrationStatus enum values"""
        assert RegistrationStatus.FORM_INCOMPLETE.value == "form_incomplete"
        assert RegistrationStatus.WAITING_FOR_PARTNER.value == "waiting_for_partner"
        assert RegistrationStatus.PARTNER_REMINDER_SENT.value == "partner_reminder_sent"
        assert RegistrationStatus.READY_FOR_REVIEW.value == "ready_for_review"
        assert RegistrationStatus.APPROVED.value == "approved"
        assert RegistrationStatus.REJECTED.value == "rejected"
        assert RegistrationStatus.PAYMENT_PENDING.value == "payment_pending"
        assert RegistrationStatus.PAYMENT_CONFIRMED.value == "payment_confirmed"
        assert RegistrationStatus.GROUP_OPENED.value == "group_opened"
        assert RegistrationStatus.CANCELLED.value == "cancelled"
    
    def test_status_enum(self):
        """Test Status enum values"""
        assert Status.PENDING.value == "pending"
        assert Status.APPROVED.value == "approved"
        assert Status.REJECTED.value == "rejected"
        assert Status.CANCELLED.value == "cancelled"
        assert Status.UNINTERESTED.value == "uninterested"
    
    def test_registration_stage_enum(self):
        """Test RegistrationStage enum values"""
        assert RegistrationStage.FORM.value == "form"
        assert RegistrationStage.PARTNER_FORM.value == "partner_form"
        assert RegistrationStage.GET_TO_KNOW.value == "get_to_know"
        assert RegistrationStage.PAYMENT.value == "payment"
        assert RegistrationStage.GROUP.value == "group"
        assert RegistrationStage.ARRIVED.value == "arrived"
    
    def test_create_registration_dto(self):
        """Test CreateRegistrationDTO creation"""
        dto = CreateRegistrationDTO(
            user_id="user123",
            event_id="event456"
        )
        
        assert dto.user_id == "user123"
        assert dto.event_id == "event456"
        assert dto.status == RegistrationStatus.FORM_INCOMPLETE.value
        assert dto.id is not None  # Should be auto-generated
    
    def test_create_registration_dto_with_custom_values(self):
        """Test CreateRegistrationDTO with custom values"""
        dto = CreateRegistrationDTO(
            user_id="user123",
            event_id="event456",
            id="custom_id",
            status=RegistrationStatus.APPROVED.value
        )
        
        assert dto.user_id == "user123"
        assert dto.event_id == "event456"
        assert dto.id == "custom_id"
        assert dto.status == RegistrationStatus.APPROVED.value
    
    def test_registration_data(self):
        """Test RegistrationData creation"""
        data = RegistrationData(
            id="reg123",
            event_id="event456",
            user_id="user789",
            status="approved",
            partner_telegram_link="@partner",
            payment_status="paid",
            payment_method="credit_card",
            registration_date="2024-01-01",
            payment_date="2024-01-02",
            partner_or_single="partner",
            intro_opt_in="yes",
            intro_text="Hello world",
            intro_posted_at="2024-01-03",
            created_at="2024-01-01",
            updated_at="2024-01-01",
            would_you_like_to_register=True,
            last_sti_test="2024-01-01",
            bdsm_declaration=True,
            is_play_with_partner_only=False,
            desired_play_partners="anyone",
            contact_type="telegram",
            contact_type_other="",
            share_bdsm_interests=True,
            alcohol_in_event="yes",
            agree_participant_commitment=True,
            enthusiastic_verbal_consent_commitment=True,
            agree_line_rules=True,
            wants_to_helper=False,
            helper_shifts="",
            wants_to_DM=False,
            DM_shifts="",
            get_to_know_status="complete",
            group_status="open",
            arrived=False,
            ginger_first_try=True,
            form_complete=True
        )
        
        assert data.id == "reg123"
        assert data.event_id == "event456"
        assert data.user_id == "user789"
        assert data.status == "approved"
        assert data.partner_telegram_link == "@partner"
        assert data.payment_status == "paid"
        assert data.payment_method == "credit_card"
        assert data.would_you_like_to_register is True
        assert data.bdsm_declaration is True
        assert data.is_play_with_partner_only is False
        assert data.share_bdsm_interests is True
        assert data.alcohol_in_event == "yes"
        assert data.agree_participant_commitment is True
        assert data.enthusiastic_verbal_consent_commitment is True
        assert data.agree_line_rules is True
        assert data.wants_to_helper is False
        assert data.wants_to_DM is False
        assert data.arrived is False
        assert data.ginger_first_try is True
        assert data.form_complete is True
    
    def test_partner_info(self):
        """Test PartnerInfo creation"""
        partner = PartnerInfo(
            name="Test Partner",
            status="pending",
            registration_complete=False,
            reminder_sent=True,
            telegram_linked=True
        )
        
        assert partner.name == "Test Partner"
        assert partner.status == "pending"
        assert partner.registration_complete is False
        assert partner.reminder_sent is True
        assert partner.telegram_linked is True
    
    def test_partner_info_defaults(self):
        """Test PartnerInfo with default values"""
        partner = PartnerInfo(
            name="Test Partner",
            status="pending",
            registration_complete=False
        )
        
        assert partner.name == "Test Partner"
        assert partner.status == "pending"
        assert partner.registration_complete is False
        assert partner.reminder_sent is False
        assert partner.telegram_linked is False


class TestUserModels:
    """Test suite for user-related models"""
    
    def test_create_user_from_telegram_dto(self):
        """Test CreateUserFromTelegramDTO creation"""
        dto = CreateUserFromTelegramDTO(
            full_name="John Doe",
            telegram_user_id="123456789",
            telegram_username="@johndoe",
            language="en"
        )
        
        assert dto.full_name == "John Doe"
        assert dto.telegram_user_id == "123456789"
        assert dto.telegram_username == "@johndoe"
        assert dto.language == "en"
    
    def test_create_user_from_telegram_dto_without_username(self):
        """Test CreateUserFromTelegramDTO without username"""
        dto = CreateUserFromTelegramDTO(
            full_name="John Doe",
            telegram_user_id="123456789",
            telegram_username=None,
            language="he"
        )
        
        assert dto.full_name == "John Doe"
        assert dto.telegram_user_id == "123456789"
        assert dto.telegram_username is None
        assert dto.language == "he"


class TestEventModels:
    """Test suite for event-related models"""
    
    def test_event(self):
        """Test Event creation"""
        event = EventDTO(
            id="event123",
            name="Test Event",
            description="Test Description",
            start_date="2024-01-01",
            start_time="18:00",
            end_date="2024-01-01",
            end_time="22:00",
            location="Test Location",
            schedule="18:00-22:00",
            event_type="workshop",
            price_single="100",
            price_couple="180",
            price_include="Food included",
            theme="Test Theme",
            max_participants="20",
            status="active",
            participant_commitment="Required",
            line_rules="Test rules",
            place_rules="Test place rules",
            is_public=True,
            main_group_id="group1",
            singles_group_id="singles1",
            created_at="2024-01-01 10:00:00",
            updated_at="2024-01-01 10:00:00"
        )
        
        assert event.id == "event123"
        assert event.name == "Test Event"
        assert event.description == "Test Description"
        assert event.start_date == "2024-01-01"
        assert event.start_time == "18:00"
        assert event.end_date == "2024-01-01"
        assert event.end_time == "22:00"
        assert event.location == "Test Location"
        assert event.schedule == "18:00-22:00"
        assert event.event_type == "workshop"
        assert event.price_single == "100"
        assert event.price_couple == "180"
        assert event.price_include == "Food included"
        assert event.theme == "Test Theme"
        assert event.max_participants == "20"
        assert event.status == "active"
        assert event.participant_commitment == "Required"
        assert event.line_rules == "Test rules"
        assert event.place_rules == "Test place rules"
        assert event.is_public is True
        assert event.main_group_id == "group1"
        assert event.singles_group_id == "singles1"
        assert event.created_at == "2024-01-01 10:00:00"
        assert event.updated_at == "2024-01-01 10:00:00"


class TestTelegramPollFields:
    """Test suite for Telegram poll field models"""
    
    def test_telegram_poll_fields(self):
        """Test TelegramPollFields creation"""
        poll_fields = TelegramPollFields(
            question="What is your favorite color?",
            options=["Red", "Blue", "Green"],
            is_anonymous=False,
            allows_multiple_answers=True
        )
        
        assert poll_fields.question == "What is your favorite color?"
        assert poll_fields.options == ["Red", "Blue", "Green"]
        assert poll_fields.is_anonymous is False
        assert poll_fields.allows_multiple_answers is True
    
    def test_telegram_poll_data(self):
        """Test TelegramPollData creation"""
        poll_data = TelegramPollData(
            id="poll123",
            question_field="test_field",
            question="Test question",
            options=["Option 1", "Option 2"],
            chat_id="123456789",
            message_id=456,
            creator="test_user",
            type="quiz",
            votes={0: [123, 456], 1: [789]}
        )
        
        assert poll_data.id == "poll123"
        assert poll_data.question_field == "test_field"
        assert poll_data.question == "Test question"
        assert poll_data.options == ["Option 1", "Option 2"]
        assert poll_data.chat_id == "123456789"
        assert poll_data.message_id == 456
        assert poll_data.creator == "test_user"
        assert poll_data.type == "quiz"
        assert poll_data.votes == {0: [123, 456], 1: [789]}


class TestFormFlowModels:
    """Test suite for form flow models"""
    
    def test_question_title(self):
        """Test QuestionTitle creation"""
        title = Text(en="What is your name?", he="מה השם שלך?")
        
        assert title.en == "What is your name?"
        assert title.he == "מה השם שלך?"
        assert title.get("en") == "What is your name?"
        assert title.get("he") == "מה השם שלך?"
        assert title.get("fr") == "What is your name?"  # Falls back to English
    
    def test_question_placeholder(self):
        """Test QuestionPlaceholder creation"""
        placeholder = Text(en="Enter your name", he="הכנס את השם שלך")
        
        assert placeholder.en == "Enter your name"
        assert placeholder.he == "הכנס את השם שלך"
        assert placeholder.get("en") == "Enter your name"
        assert placeholder.get("he") == "הכנס את השם שלך"
        assert placeholder.get("fr") == "Enter your name"  # Falls back to English
    
    def test_question_option(self):
        """Test QuestionOption creation"""
        option = QuestionOption(
            value="yes",
            text=Text(en="Yes", he="כן")
        )
        
        assert option.value == "yes"
        assert option.text.en == "Yes"
        assert option.text.he == "כן"
    
    def test_question_definition_boolean(self):
        """Test QuestionDefinition with boolean type"""
        question = QuestionDefinition(
            question_id="test_question",
            title=Text(en="Do you agree?", he="האם אתה מסכים?"),
            question_type=QuestionType.BOOLEAN,
            required=True,
            save_to="user_data",
            options=[
                QuestionOption(value="yes", text=Text(en="Yes", he="כן")),
                QuestionOption(value="no", text=Text(en="No", he="לא"))
            ]
        )
        
        assert question.question_id == "test_question"
        assert question.title.en == "Do you agree?"
        assert question.title.he == "האם אתה מסכים?"
        assert question.question_type == QuestionType.BOOLEAN
        assert question.required is True
        assert question.save_to == "user_data"
        assert len(question.options) == 2
        assert question.options[0].value == "yes"
        assert question.options[1].value == "no"
    
    def test_question_definition_text(self):
        """Test QuestionDefinition with text type"""
        question = QuestionDefinition(
            question_id="name_question",
            title=Text(en="What is your name?", he="מה השם שלך?"),
            question_type=QuestionType.TEXT,
            required=True,
            save_to="user_data",
            placeholder=Text(en="Enter your full name", he="הכנס את השם המלא שלך")
        )
        
        assert question.question_id == "name_question"
        assert question.title.en == "What is your name?"
        assert question.question_type == QuestionType.TEXT
        assert question.required is True
        assert question.save_to == "user_data"
        assert question.placeholder.en == "Enter your full name"
        assert question.placeholder.he == "הכנס את השם המלא שלך"
        assert question.options is None
    
    def test_question_definition_select(self):
        """Test QuestionDefinition with select type"""
        question = QuestionDefinition(
            question_id="color_question",
            title=Text(en="What is your favorite color?", he="מה הצבע האהוב עליך?"),
            question_type=QuestionType.SELECT,
            required=False,
            save_to="preferences",
            options=[
                QuestionOption(value="red", text=Text(en="Red", he="אדום")),
                QuestionOption(value="blue", text=Text(en="Blue", he="כחול")),
                QuestionOption(value="green", text=Text(en="Green", he="ירוק"))
            ]
        )
        
        assert question.question_id == "color_question"
        assert question.title.en == "What is your favorite color?"
        assert question.question_type == QuestionType.SELECT
        assert question.required is False
        assert question.save_to == "preferences"
        assert len(question.options) == 3
        assert question.options[0].value == "red"
        assert question.options[1].value == "blue"
        assert question.options[2].value == "green"
    
    def test_question_definition_multi_select(self):
        """Test QuestionDefinition with multi-select type"""
        question = QuestionDefinition(
            question_id="interests_question",
            title=Text(en="What are your interests?", he="מה התחומי העניין שלך?"),
            question_type=QuestionType.MULTI_SELECT,
            required=False,
            save_to="interests",
            options=[
                QuestionOption(value="sports", text=Text(en="Sports", he="ספורט")),
                QuestionOption(value="music", text=Text(en="Music", he="מוזיקה")),
                QuestionOption(value="reading", text=Text(en="Reading", he="קריאה"))
            ]
        )
        
        assert question.question_id == "interests_question"
        assert question.title.en == "What are your interests?"
        assert question.question_type == QuestionType.MULTI_SELECT
        assert question.required is False
        assert question.save_to == "interests"
        assert len(question.options) == 3
    
    def test_question_definition_date(self):
        """Test QuestionDefinition with date type"""
        question = QuestionDefinition(
            question_id="birth_date",
            title=Text(en="When were you born?", he="מתי נולדת?"),
            question_type=QuestionType.DATE,
            required=True,
            save_to="personal_info"
        )
        
        assert question.question_id == "birth_date"
        assert question.title.en == "When were you born?"
        assert question.question_type == QuestionType.DATE
        assert question.required is True
        assert question.save_to == "personal_info"
        assert question.options is None
        assert question.placeholder is None


class TestModelValidation:
    """Test suite for model validation"""
    
    def test_registration_data_validation(self):
        """Test RegistrationData field validation"""
        # Test that all required fields are present
        data = RegistrationData(
            id="reg123",
            event_id="event456",
            user_id="user789",
            status="approved",
            partner_telegram_link="@partner",
            payment_status="paid",
            payment_method="credit_card",
            registration_date="2024-01-01",
            payment_date="2024-01-02",
            partner_or_single="partner",
            intro_opt_in="yes",
            intro_text="Hello world",
            intro_posted_at="2024-01-03",
            created_at="2024-01-01",
            updated_at="2024-01-01",
            would_you_like_to_register=True,
            last_sti_test="2024-01-01",
            bdsm_declaration=True,
            is_play_with_partner_only=False,
            desired_play_partners="anyone",
            contact_type="telegram",
            contact_type_other="",
            share_bdsm_interests=True,
            alcohol_in_event="yes",
            agree_participant_commitment=True,
            enthusiastic_verbal_consent_commitment=True,
            agree_line_rules=True,
            wants_to_helper=False,
            helper_shifts="",
            wants_to_DM=False,
            DM_shifts="",
            get_to_know_status="complete",
            group_status="open",
            arrived=False
        )
        
        # Test that boolean fields work correctly
        assert isinstance(data.would_you_like_to_register, bool)
        assert isinstance(data.bdsm_declaration, bool)
        assert isinstance(data.is_play_with_partner_only, bool)
        assert isinstance(data.share_bdsm_interests, bool)
        assert isinstance(data.agree_participant_commitment, bool)
        assert isinstance(data.enthusiastic_verbal_consent_commitment, bool)
        assert isinstance(data.agree_line_rules, bool)
        assert isinstance(data.wants_to_helper, bool)
        assert isinstance(data.wants_to_DM, bool)
        assert isinstance(data.arrived, bool)
        assert isinstance(data.ginger_first_try, bool)
        assert isinstance(data.form_complete, bool)
    
    def test_question_definition_validation(self):
        """Test QuestionDefinition field validation"""
        question = QuestionDefinition(
            question_id="test_question",
            title=Text(en="Test question", he="שאלה לבדיקה"),
            question_type=QuestionType.BOOLEAN,
            required=True,
            save_to="test_data",
            options=[
                QuestionOption(value="yes", text=Text(en="Yes", he="כן")),
                QuestionOption(value="no", text=Text(en="No", he="לא"))
            ]
        )
        
        # Test that enum values work correctly
        assert question.question_type == QuestionType.BOOLEAN
        assert isinstance(question.required, bool)
        assert isinstance(question.save_to, str)
        assert isinstance(question.options, list)
        assert len(question.options) == 2
        
        # Test that options have correct structure
        for option in question.options:
            assert hasattr(option, 'value')
            assert hasattr(option, 'text')
            assert hasattr(option.text, 'en')
            assert hasattr(option.text, 'he')
    
    def test_enum_values_consistency(self):
        """Test that enum values are consistent and unique"""
        # Test RegistrationStatus enum
        status_values = [status.value for status in RegistrationStatus]
        assert len(status_values) == len(set(status_values))  # All values are unique
        
        # Test Status enum
        status_values = [status.value for status in Status]
        assert len(status_values) == len(set(status_values))  # All values are unique
        
        # Test RegistrationStage enum
        stage_values = [stage.value for stage in RegistrationStage]
        assert len(stage_values) == len(set(stage_values))  # All values are unique
        
        # Test QuestionType enum
        type_values = [qtype.value for qtype in QuestionType]
        assert len(type_values) == len(set(type_values))  # All values are unique 