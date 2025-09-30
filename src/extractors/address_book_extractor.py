"""
macOS Address Book / Contacts extractor for Avatar-Engine
Extracts person information and nicknames from macOS Contacts
Last Updated: September 29, 2025
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

try:
    import Contacts
    import AddressBook  # For legacy support
    from Foundation import NSPredicate
    CONTACTS_AVAILABLE = True
except ImportError:
    CONTACTS_AVAILABLE = False
    logger.warning("macOS Contacts framework not available. Address Book extraction disabled.")

from models.graph_models import Person, Nickname, NicknameSource, NicknameType


class AddressBookExtractor:
    """Extract contacts and nicknames from macOS Address Book/Contacts"""
    
    def __init__(self, mock_mode=False):
        """
        Initialize the Address Book extractor
        
        Args:
            mock_mode: If True, use mock data instead of real contacts (for testing)
        """
        self.mock_mode = mock_mode
        self.contacts_cache = {}
        
        # Common nickname patterns
        self.nickname_patterns = {
            # Formal to informal mappings
            'robert': ['bob', 'rob', 'robbie', 'bobby'],
            'william': ['will', 'bill', 'billy', 'willie', 'liam'],
            'richard': ['rick', 'dick', 'rich', 'ricky'],
            'michael': ['mike', 'mikey', 'mick', 'mickey'],
            'joseph': ['joe', 'joey', 'jo'],
            'james': ['jim', 'jimmy', 'jamie'],
            'john': ['jack', 'johnny', 'jon'],
            'elizabeth': ['liz', 'lizzie', 'beth', 'betty', 'eliza', 'libby'],
            'margaret': ['maggie', 'peggy', 'meg', 'marge'],
            'katherine': ['kate', 'katie', 'kathy', 'kat', 'kit'],
            'alexander': ['alex', 'al', 'sandy', 'xander', 'sasha'],
            'christopher': ['chris', 'kit', 'topher'],
            'nicholas': ['nick', 'nicky', 'nico'],
            'benjamin': ['ben', 'benny', 'benji'],
            'samuel': ['sam', 'sammy'],
            'daniel': ['dan', 'danny'],
            'matthew': ['matt', 'matty'],
            'andrew': ['andy', 'drew'],
            'thomas': ['tom', 'tommy'],
            'charles': ['charlie', 'chuck', 'chas'],
            'edward': ['ed', 'eddie', 'ted', 'teddy', 'ned'],
        }
        
        # Reverse mapping for finding formal names from nicknames
        self.formal_from_nickname = {}
        for formal, nicknames in self.nickname_patterns.items():
            for nickname in nicknames:
                self.formal_from_nickname[nickname.lower()] = formal
        
        # Only initialize Contacts store if not in mock mode
        if not mock_mode:
            if not CONTACTS_AVAILABLE:
                logger.error("macOS Contacts framework is not available.")
                logger.error("Please install the required packages:")
                logger.error("  pip3 install pyobjc-framework-Contacts pyobjc-framework-AddressBook")
                logger.error("Or use mock mode: AddressBookExtractor(mock_mode=True)")
                raise ImportError("macOS Contacts framework is not available. Use mock_mode=True for testing.")
            
            self.store = Contacts.CNContactStore.new()

    def request_access(self) -> bool:
        """Request access to Contacts if needed"""
        if self.mock_mode:
            return True
            
        try:
            # Check authorization status
            auth_status = Contacts.CNContactStore.authorizationStatusForEntityType_(
                Contacts.CNEntityTypeContacts
            )
            
            if auth_status == Contacts.CNAuthorizationStatusAuthorized:
                return True
            elif auth_status == Contacts.CNAuthorizationStatusNotDetermined:
                # Request access
                granted, error = self.store.requestAccessForEntityType_completionHandler_(
                    Contacts.CNEntityTypeContacts,
                    None
                )
                if granted:
                    logger.info("Contacts access granted")
                    return True
                else:
                    logger.error(f"Contacts access denied: {error}")
                    return False
            else:
                logger.error("Contacts access denied or restricted")
                return False
        except Exception as e:
            logger.error(f"Error requesting contacts access: {e}")
            return False

    def extract_all_contacts(self) -> List[Person]:
        """Extract all contacts from Address Book or return mock data"""
        if self.mock_mode:
            logger.info("Using mock data for testing")
            return self._get_mock_contacts()
        
        if not self.request_access():
            logger.error("Cannot access contacts without permission")
            logger.info("Tip: Use mock_mode=True to test with sample data")
            return []
        
        persons = []
        
        try:
            # Define which contact properties to fetch
            keys_to_fetch = [
                Contacts.CNContactGivenNameKey,
                Contacts.CNContactFamilyNameKey,
                Contacts.CNContactMiddleNameKey,
                Contacts.CNContactNicknameKey,
                Contacts.CNContactPhoneticGivenNameKey,
                Contacts.CNContactPhoneticFamilyNameKey,
                Contacts.CNContactEmailAddressesKey,
                Contacts.CNContactPhoneNumbersKey,
                Contacts.CNContactOrganizationNameKey,
                Contacts.CNContactJobTitleKey,
                Contacts.CNContactNoteKey,
                Contacts.CNContactIdentifierKey,
                Contacts.CNContactSocialProfilesKey,
                Contacts.CNContactInstantMessageAddressesKey,
            ]
            
            # Create fetch request
            fetch_request = Contacts.CNContactFetchRequest.alloc().initWithKeysToFetch_(
                keys_to_fetch
            )
            
            # Fetch all contacts
            contacts = []
            success = self.store.enumerateContactsWithFetchRequest_error_usingBlock_(
                fetch_request,
                None,
                lambda contact, stop: contacts.append(contact) or False
            )
            
            if success:
                logger.info(f"Found {len(contacts)} contacts in Address Book")
                
                for contact in contacts:
                    person = self._contact_to_person(contact)
                    if person:
                        persons.append(person)
                        self.contacts_cache[person.id] = person
            else:
                logger.error("Failed to enumerate contacts")
                
        except Exception as e:
            logger.error(f"Error extracting contacts: {e}")
        
        return persons

    def _contact_to_person(self, contact) -> Optional[Person]:
        """Convert a CNContact to Person model"""
        try:
            # Extract basic name information
            given_name = str(contact.givenName()) if contact.givenName() else ""
            family_name = str(contact.familyName()) if contact.familyName() else ""
            middle_name = str(contact.middleName()) if contact.middleName() else None
            
            # Build full name
            full_name_parts = [p for p in [given_name, middle_name, family_name] if p]
            full_name = " ".join(full_name_parts)
            
            if not full_name:
                return None
            
            # Extract contact info
            emails = self._extract_emails(contact)
            phones = self._extract_phones(contact)
            
            # Create person
            person = Person(
                id=str(contact.identifier()),
                full_name=full_name,
                first_name=given_name if given_name else None,
                last_name=family_name if family_name else None,
                middle_name=middle_name,
                email=emails,
                phone=phones,
                organization=str(contact.organizationName()) if contact.organizationName() else None,
                job_title=str(contact.jobTitle()) if contact.jobTitle() else None,
                address_book_id=str(contact.identifier())
            )
            
            # Extract nicknames
            nicknames = self._extract_nicknames(contact, person)
            for nickname in nicknames:
                person.add_nickname(nickname)
            
            return person
            
        except Exception as e:
            logger.error(f"Error converting contact to person: {e}")
            return None

    def _extract_nicknames(self, contact, person: Person) -> List[Nickname]:
        """Extract all nicknames from a contact"""
        nicknames = []
        
        # 1. Explicit nickname field
        if contact.nickname():
            nickname_str = str(contact.nickname()).strip()
            if nickname_str:
                nicknames.append(Nickname(
                    name=nickname_str,
                    source=NicknameSource.ADDRESS_BOOK,
                    nickname_type=NicknameType.GIVEN,
                    confidence=1.0
                ))
        
        # 2. Phonetic names (often used for nicknames in some cultures)
        if contact.phoneticGivenName():
            phonetic_name = str(contact.phoneticGivenName()).strip()
            if phonetic_name and phonetic_name != person.first_name:
                nicknames.append(Nickname(
                    name=phonetic_name,
                    source=NicknameSource.ADDRESS_BOOK,
                    nickname_type=NicknameType.CULTURAL,
                    confidence=0.9
                ))
        
        # 3. Extract from notes field
        if contact.note():
            note_nicknames = self._extract_nicknames_from_note(str(contact.note()))
            nicknames.extend(note_nicknames)
        
        # 4. Social media handles
        social_nicknames = self._extract_social_handles(contact)
        nicknames.extend(social_nicknames)
        
        # 5. Infer common nicknames from first name
        if person.first_name:
            inferred = self._infer_common_nicknames(person.first_name)
            nicknames.extend(inferred)
        
        # 6. Extract initials
        initials = self._create_initials_nickname(person)
        if initials:
            nicknames.append(initials)
        
        return nicknames

    def _extract_nicknames_from_note(self, note: str) -> List[Nickname]:
        """Extract nicknames from notes field using patterns"""
        nicknames = []
        
        # Patterns to look for nicknames in notes
        patterns = [
            r'(?:nickname|nick|aka|also known as|goes by|called)[:\s]+([^\n,;]+)',
            r'["\']([^"\']+)["\']',  # Names in quotes
            r'\(([^)]+)\)',  # Names in parentheses
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, note, re.IGNORECASE)
            for match in matches:
                potential_nickname = match.group(1).strip()
                # Basic validation
                if 2 <= len(potential_nickname) <= 30 and not potential_nickname.isdigit():
                    nicknames.append(Nickname(
                        name=potential_nickname,
                        source=NicknameSource.ADDRESS_BOOK,
                        nickname_type=NicknameType.GIVEN,
                        confidence=0.8,
                        context="Extracted from notes"
                    ))
        
        return nicknames

    def _extract_social_handles(self, contact) -> List[Nickname]:
        """Extract social media handles as potential nicknames"""
        nicknames = []
        
        try:
            # Social profiles
            if contact.socialProfiles():
                for profile in contact.socialProfiles():
                    username = profile.value().username()
                    if username:
                        username_str = str(username).strip()
                        if username_str and not '@' in username_str:  # Skip email-like handles
                            nicknames.append(Nickname(
                                name=username_str,
                                source=NicknameSource.ADDRESS_BOOK,
                                nickname_type=NicknameType.SOCIAL,
                                confidence=0.7,
                                context=f"Social: {profile.value().service()}"
                            ))
            
            # Instant messaging addresses
            if contact.instantMessageAddresses():
                for im in contact.instantMessageAddresses():
                    username = im.value().username()
                    if username:
                        username_str = str(username).strip()
                        if username_str and '@' not in username_str:
                            nicknames.append(Nickname(
                                name=username_str,
                                source=NicknameSource.ADDRESS_BOOK,
                                nickname_type=NicknameType.SOCIAL,
                                confidence=0.7,
                                context=f"IM: {im.value().service()}"
                            ))
                            
        except Exception as e:
            logger.debug(f"Error extracting social handles: {e}")
        
        return nicknames

    def _infer_common_nicknames(self, first_name: str) -> List[Nickname]:
        """Infer common nicknames based on first name"""
        nicknames = []
        first_lower = first_name.lower()
        
        # Check if this name has common nicknames
        if first_lower in self.nickname_patterns:
            for nick in self.nickname_patterns[first_lower]:
                nicknames.append(Nickname(
                    name=nick.capitalize(),
                    source=NicknameSource.INFERRED,
                    nickname_type=NicknameType.DIMINUTIVE,
                    confidence=0.5,  # Lower confidence for inferred
                    context="Common nickname pattern"
                ))
        
        # Check for simple diminutives (first 3-4 letters)
        if len(first_name) > 5:
            # Try first 3 letters
            short_name = first_name[:3]
            if short_name.lower() != first_lower:
                nicknames.append(Nickname(
                    name=short_name,
                    source=NicknameSource.INFERRED,
                    nickname_type=NicknameType.DIMINUTIVE,
                    confidence=0.3,
                    context="Shortened version"
                ))
        
        return nicknames

    def _create_initials_nickname(self, person: Person) -> Optional[Nickname]:
        """Create initials-based nickname"""
        initials_parts = []
        
        if person.first_name:
            initials_parts.append(person.first_name[0].upper())
        if person.middle_name:
            initials_parts.append(person.middle_name[0].upper())
        if person.last_name:
            initials_parts.append(person.last_name[0].upper())
        
        if len(initials_parts) >= 2:
            initials = "".join(initials_parts)
            return Nickname(
                name=initials,
                source=NicknameSource.INFERRED,
                nickname_type=NicknameType.INITIALS,
                confidence=0.6,
                context="Initials"
            )
        
        return None

    def _extract_emails(self, contact) -> List[str]:
        """Extract email addresses from contact"""
        emails = []
        
        try:
            if contact.emailAddresses():
                for email in contact.emailAddresses():
                    email_str = str(email.value()).strip()
                    if email_str:
                        emails.append(email_str)
        except Exception as e:
            logger.debug(f"Error extracting emails: {e}")
        
        return emails

    def _extract_phones(self, contact) -> List[str]:
        """Extract phone numbers from contact"""
        phones = []
        
        try:
            if contact.phoneNumbers():
                for phone in contact.phoneNumbers():
                    phone_str = str(phone.value().stringValue()).strip()
                    if phone_str:
                        phones.append(phone_str)
        except Exception as e:
            logger.debug(f"Error extracting phones: {e}")
        
        return phones

    def find_person_by_nickname(self, nickname: str) -> List[Person]:
        """Find persons by nickname"""
        matches = []
        nickname_lower = nickname.lower()
        
        for person in self.contacts_cache.values():
            for nick in person.nicknames:
                if nick.name.lower() == nickname_lower:
                    matches.append(person)
                    break
        
        return matches
    
    def _get_mock_contacts(self) -> List[Person]:
        """Get mock contacts for testing"""
        mock_persons = []
        
        # Person 1: Robert Smith
        person1 = Person(
            id="mock_001",
            full_name="Robert Smith",
            first_name="Robert",
            last_name="Smith",
            email=["robert.smith@example.com", "bob@company.com"],
            phone=["+1-555-0101"],
            organization="Tech Corp",
            job_title="Software Engineer",
            address_book_id="mock_001"
        )
        
        # Add nicknames based on patterns
        nicknames1 = self._infer_common_nicknames("Robert")
        for nick in nicknames1:
            person1.add_nickname(nick)
        
        # Add explicit nickname
        person1.add_nickname(Nickname(
            name="Bob",
            source=NicknameSource.ADDRESS_BOOK,
            nickname_type=NicknameType.DIMINUTIVE,
            confidence=1.0,
            frequency=50
        ))
        
        # Add initials
        initials = self._create_initials_nickname(person1)
        if initials:
            person1.add_nickname(initials)
        
        mock_persons.append(person1)
        self.contacts_cache[person1.id] = person1
        
        # Person 2: Elizabeth Johnson
        person2 = Person(
            id="mock_002",
            full_name="Elizabeth Johnson",
            first_name="Elizabeth",
            last_name="Johnson",
            email=["liz@example.com"],
            phone=["+1-555-0102"],
            organization="Design Studios",
            job_title="Creative Director",
            address_book_id="mock_002"
        )
        
        # Add common nicknames
        nicknames2 = self._infer_common_nicknames("Elizabeth")
        for nick in nicknames2:
            person2.add_nickname(nick)
        
        person2.add_nickname(Nickname(
            name="Liz",
            source=NicknameSource.ADDRESS_BOOK,
            nickname_type=NicknameType.DIMINUTIVE,
            confidence=1.0,
            frequency=40
        ))
        
        mock_persons.append(person2)
        self.contacts_cache[person2.id] = person2
        
        # Person 3: Michael Chen
        person3 = Person(
            id="mock_003",
            full_name="Michael Chen",
            first_name="Michael",
            last_name="Chen",
            middle_name="Wei",
            email=["mchen@university.edu"],
            phone=["+1-555-0103"],
            organization="State University",
            job_title="Professor",
            address_book_id="mock_003"
        )
        
        # Add nicknames
        nicknames3 = self._infer_common_nicknames("Michael")
        for nick in nicknames3:
            person3.add_nickname(nick)
        
        person3.add_nickname(Nickname(
            name="Professor Chen",
            source=NicknameSource.CONVERSATION,
            nickname_type=NicknameType.PROFESSIONAL,
            confidence=0.9,
            frequency=25
        ))
        
        mock_persons.append(person3)
        self.contacts_cache[person3.id] = person3
        
        logger.info(f"Generated {len(mock_persons)} mock contacts with nicknames")
        return mock_persons
