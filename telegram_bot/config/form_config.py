"""
Form Configuration - Configurable form definitions for event registration
This file contains all question definitions and can be customized for different event organizers.
"""

from typing import Dict, List, Any
from ..models.form_flow import (
    QuestionType, ValidationRuleType, Text, ValidationRule,
    SkipConditionItem, SkipCondition, QuestionOption, QuestionDefinition
)


class FormConfig:
    """Configuration class for form definitions."""
    
    @staticmethod
    def get_question_definitions() -> Dict[str, QuestionDefinition]:
        """Get all question definitions for the form."""
        skip = Text(he="ניתן לדלג על השאלה. רשמו 'המשך'", en="you can skip the question. write 'continue'")
        
        return {
            # 1. Language selection (every time)
            "language": QuestionDefinition(
                question_id="language",
                question_type=QuestionType.SELECT,
                title=Text(
                    he="באיזו שפה תרצה למלא את הטופס?",
                    en="In which language would you like to fill the form?"),
                required=True,
                save_to="Users",
                order=1,
                options=[
                    QuestionOption(value="he", text=Text(he="עברית", en="Hebrew")),
                    QuestionOption(value="en", text=Text(he="English", en="English"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(
                            he="אנא בחר שפה",
                            en="Please select a language")
                    )
                ]
            ),
            
            # 2. Event type
            "interested_in_event_types": QuestionDefinition(
                question_id="interested_in_event_types",
                question_type=QuestionType.MULTI_SELECT,
                title=Text(he="מה סוגי האירועים שתרצה להשתתף בהם?", en="What type of events would you like to participate in?"),
                required=True,
                save_to="Users",
                order=2,
                options=[
                    QuestionOption(value="play", text=Text(he="משחק", en="Play")),
                    QuestionOption(value="cuddle", text=Text(he="כירבולייה", en="Cuddle"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אירוע", en="Please select an event")
                    )
                ]
            ),
            
            # 3. Event selection (every time)
            "event_selection": QuestionDefinition(
                question_id="event_selection",
                question_type=QuestionType.SELECT,
                title=Text(he="לאיזה אירוע תרצה להירשם?", en="To which event would you like to register?"),
                required=True,
                save_to="Registrations",
                order=3,
                options=[],  # Will be populated dynamically
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אירוע", en="Please select an event")
                    )
                ]
            ),
            
            # 4. would you like to register?
            "would_you_like_to_register": QuestionDefinition(
                question_id="would_you_like_to_register",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם תרצה להירשם לאירוע?", en="Would you like to register to this event?"),
                required=True,
                save_to="Registrations",
                order=4,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אירוע", en="Please select an event")
                    )
                ]
            ),
            
            # 5. Full name (new users only)
            "full_name": QuestionDefinition(
                question_id="full_name",
                question_type=QuestionType.TEXT,
                title=Text(he="מה השם המלא שלך?", en="What is your full name?"),
                required=True,
                save_to="Users",
                order=5,
                placeholder=Text(he="הזן שם מלא", en="Enter full name"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="user_exists", field="telegram_id")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן את שמך המלא", en="Please enter your full name")
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.MIN_LENGTH,
                        params={"min": 2},
                        error_message=Text(he="השם חייב להכיל לפחות 2 תווים", en="Name must contain at least 2 characters")
                    )
                ]
            ),
            
            # 6. relevant experience
            "relevent_experience": QuestionDefinition(
                question_id="relevent_experience",
                question_type=QuestionType.TEXT,
                title=Text(he="מה רמת הניסיון שלך באירועים דומים?", en="What is your experience with similar events?"),
                required=True,
                save_to="Users",
                order=6,
                placeholder=Text(he="למשל: משחק בכירבולייה, משחק במשחקים בודדים, משחק במשחקים בצניחה, משחק במשחקים במשחקים בכירבולייה", en="e.g., Play in cuddle, Play in solo, Play in cuddle, Play in bdsm, Play in bdsm in cuddle, Play in bdsm in solo"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן רמת ניסיון", en="Please enter experience")
                    )
                ]
            ),
            
            # 7. partner or single
            "partner_or_single": QuestionDefinition(
                question_id="partner_or_single",
                question_type=QuestionType.SELECT,
                title=Text(he="האם אתה/את מגיע/ה לבד או עם פרטנר?", en="Are you coming alone or with a partner?"),
                required=True,
                save_to="Registrations",
                order=7,
                options=[
                    QuestionOption(value="single", text=Text(he="לבד", en="Alone")),
                    QuestionOption(value="partner", text=Text(he="עם פרטנר", en="With partner"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            
            # 8. partner telegram link
            "partner_telegram_link": QuestionDefinition(
                question_id="partner_telegram_link",
                question_type=QuestionType.TELEGRAM_LINK,
                title=Text(he="אנא שתף לינק לטלגרם של הפרטנר שלך", en="Please share your partner's Telegram link"),
                required=True,
                save_to="Registrations",
                order=8,
                placeholder=Text(he="https://t.me/username Or @username", en="https://t.me/username Or @username"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="partner_or_single", value="single", operator="equals")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן לינק לטלגרם", en="Please enter Telegram link")
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.TELEGRAM_LINK,
                        error_message=Text(he="הלינק אינו תקין. אנא הזן לינק תקין לטלגרם\nhttps://t.me/username Or @username", en="Invalid link. Please enter a valid Telegram link\nhttps://t.me/username Or @username")
                    )
                ]
            ),
            
            # 9. last_sti_test
            "last_sti_test": QuestionDefinition(
                question_id="last_sti_test",
                question_type=QuestionType.DATE,
                title=Text(he="מה התאריך של בדיקת המין האחרונה שלך?", en="What is the date of your last STI test?"),
                required=True,
                save_to="Registrations",
                order=9,
                placeholder=Text(he="DD/MM/YYYY", en="DD/MM/YYYY"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="event_type", value="cuddle", operator="equals")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן תאריך בדיקה", en="Please enter test date")
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.DATE_RANGE,
                        error_message=Text(he="התאריך אינו תקין. אנא הזן תאריך תקין", en="Invalid date. Please enter a valid date")
                    )
                ]
            ),
            
            # 10. Facebook profile (new users only)
            "facebook_profile": QuestionDefinition(
                question_id="facebook_profile",
                question_type=QuestionType.FACEBOOK_LINK,
                title=Text(he="אנא שתף לינק לפרופיל הפייסבוק או האינסטגרם שלך", en="Please share a link to your Facebook OR Instagram profile"),
                required=True,
                save_to="Users",
                order=10,
                placeholder=Text(he="https://facebook.com/username Or https://instagram.com/username", en="https://facebook.com/username Or https://instagram.com/username"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="user_exists", field="telegram_id")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן לינק לפייסבוק או לאינסטגרם", en="Please enter Facebook or Instagram link")
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.FACEBOOK_LINK,
                        error_message=Text(he="הלינק אינו תקין. אנא הזן לינק תקין לפייסבוק או לאינסטגרם", en="Invalid link. Please enter a valid Facebook or Instagram link")
                    )
                ]
            ),
            
            # 11. Birth date (new users only)
            "birth_date": QuestionDefinition(
                question_id="birth_date",
                question_type=QuestionType.DATE,
                title=Text(he="מה תאריך הלידה שלך?", en="What is your birth date?"),
                required=True,
                save_to="Users",
                order=11,
                placeholder=Text(he="DD/MM/YYYY", en="DD/MM/YYYY"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="user_exists", field="telegram_id")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן תאריך לידה", en="Please enter birth date")
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.DATE_RANGE,
                        error_message=Text(he="התאריך אינו תקין. אנא הזן תאריך תקין", en="Invalid date. Please enter a valid date")
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.AGE_RANGE,
                        params={"min_age": 18, "max_age": 100},
                        error_message=Text(he="הגיל חייב להיות בין 18 ל-100", en="Age must be between 18 and 100")
                    )
                ]
            ),
            
            # 12. sexual_orientation_and_gender
            "sexual_orientation_and_gender": QuestionDefinition(
                question_id="sexual_orientation_and_gender",
                question_type=QuestionType.TEXT,
                title=Text(he="נטייה מינית ומגדר", en="Sexual orientation and gender"),
                required=True,
                save_to="Users",
                order=12,
                placeholder=Text(he="למשל: זכר סטרייט, אישה לסבית, אחר", 
                                 en="for example: male straight, female bi, other"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            
            # 13. pronouns
            "pronouns": QuestionDefinition(
                question_id="pronouns",
                question_type=QuestionType.TEXT,
                title=Text(he="מה לשון הפניה שלך?", en="What are your pronouns?"),
                required=False,
                save_to="Users",
                order=13,
                placeholder=Text(he=f"למשל: את / אתה / הם\n{skip.he}", 
                                en=f"for example: she/he/they\n{skip.en}"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ]
            ),
            
            # 14. bdsm_experience
            "bdsm_experience": QuestionDefinition(
                question_id="bdsm_experience",
                question_type=QuestionType.MULTI_SELECT,
                title=Text(he="מה רמת הניסיון שלך ב-BDSM?", en="What is your BDSM experience level?"),
                required=True,
                save_to="Users",
                order=14,
                options=[
                    QuestionOption(value="none_not_interested", text=Text(he="אין לי נסיון וגם לא מתעניין.ת בבדס\"מ", en="No experience and not interested in BDSM")),
                    QuestionOption(value="none_interested_top", text=Text(he="אין לי נסיון אבל מעניין אותי לנסות לשלוט", en="No experience but interested in trying to top")),
                    QuestionOption(value="none_interested_bottom", text=Text(he="אין לי נסיון אבל מעניין אותי לנסות להישלט", en="No experience but interested in trying to bottom")),
                    QuestionOption(value="experienced_top", text=Text(he="יש לי נסיון בתור טופ/שולט.ת", en="I have experience as a top/dominant")),
                    QuestionOption(value="experienced_bottom", text=Text(he="יש לי נסיון בתור בוטום/נשלט.ת", en="I have experience as a bottom/submissive")),
                    QuestionOption(value="other", text=Text(he="אחר", en="Other"))                
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר רמת ניסיון", en="Please select experience level")
                    )
                ]
            ),
            
            # 15. bdsm_declaration
            "bdsm_declaration": QuestionDefinition(
                question_id="bdsm_declaration",
                question_type=QuestionType.SELECT,
                title=Text(he='האירוע הינו בדסמ פרנדלי, ויכלול אקטים בדס"מים / מיניים שונים על פי רצון המשתתפים. איני מחוייב.ת להשתתף באף אקט ואסרב בנימוס אם יציעו לי אקט שאיני מעוניין.ת בו', 
                           en="The event is BDSM friendly, and will include various BDSM / sexual acts according to the wishes of the participants. I am not obliged to participate in any act and will politely refuse an offer for an act that I am not interested in."),
                required=True,
                save_to="Registrations",
                order=15,
                options=[
                    QuestionOption(value="yes", text=Text(he="כמובן", en="of course")),
                    QuestionOption(value="no", text=Text(he="לא ברור לי הסעיף, אשמח להבהרה", en="I don't understand, please clarify"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            
            # 16. is_play_with_partner_only
            "is_play_with_partner_only": QuestionDefinition(
                question_id="is_play_with_partner_only",
                question_type=QuestionType.SELECT,
                title=Text(he="האם תהיה מעוניין לשחק אך ורק עם הפרטנר שתגיעו איתו או גם עם אנשים נוספים?", 
                           en="would you like to play only with the partner you will come with or also with other people?"),
                required=True,
                save_to="Registrations",
                order=16,
                options=[
                    QuestionOption(value="partner_only", text=Text(he="רק עם פרטנר", en="Only with my partner")),
                    QuestionOption(value="other_people", text=Text(he="גם עם אחרים", en="Also with other people"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="partner_or_single", value="single", operator="equals")
                    ]
                )
            ),
            
            # 17. desired_play_partners
            "desired_play_partners": QuestionDefinition(
                question_id="desired_play_partners",
                question_type=QuestionType.MULTI_SELECT,
                title=Text(he="מי תרצה להשתתף באירוע?", en="Who would you like to participate with?"),
                required=True,
                save_to="Registrations",
                order=17,
                placeholder=Text(he="למשל: זכר, נקבה, אחר", en="e.g., male, female, other"),
                options=[
                    QuestionOption(value="all_genders", text=Text(he="יש לי עניין עם כל המגדרים", en="I am interested in all genders")),
                    QuestionOption(value="women_only", text=Text(he="יש לי עניין עם נשים* בלבד", en="I am interested in women* only")),
                    QuestionOption(value="men_only", text=Text(he="יש לי עניין עם גברים* בלבד", en="I am interested in men* only")),
                    QuestionOption(value="couples", text=Text(he="יש לי עניין עם זוג", en="I am interested in couples")),
                    QuestionOption(value="partner_dependent", text=Text(he="יש לי עניין אך זה תלוי בהסכמות של בן/בת הזוג", en="I am interested but it depends on my partner's consent"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="is_play_with_partner_only", value="partner_only", operator="equals")
                    ]
                )
            ),
            
            # 18. contact_type
            "contact_type": QuestionDefinition(
                question_id="contact_type",
                question_type=QuestionType.SELECT,
                title=Text(he="באיזה סוג מגע תהיה מעוניינ.ת?", en="What type of contact would you like?"),
                required=True,
                save_to="Registrations",
                order=18,
                options=[
                    QuestionOption(value="bdsm_only", text=Text(he="בדס״מ בלבד", en="BDSM only")),
                    QuestionOption(value="bdsm_and_sexual", text=Text(he="בדס״מ ומיניות", en="BDSM and sexual")),
                    QuestionOption(value="other", text=Text(he="אחר", en="Other"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="is_play_with_partner_only", value="partner_only", operator="equals")
                    ]
                )
            ),
            
            # 19. contact_type_other
            "contact_type_other": QuestionDefinition(
                question_id="contact_type_other",
                question_type=QuestionType.TEXT,
                title=Text(he="אנא פרט לגבי סוג המגע הרצוי", en="Please elaborate on the type of contact you would like"),
                required=True,
                save_to="Registrations",
                order=19,
                placeholder=Text(he="למשל: בדס״מ בלבד, בדס״מ ומיניות, אחר", en="e.g., BDSM only, BDSM and sexual, Other"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="contact_type", value="other", operator="equals")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ]
            ),
            
            # 20 share_bdsm_interests
            "share_bdsm_interests": QuestionDefinition(
                question_id="share_bdsm_interests",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="אשמח לשמוע על הגבולות והעדפות שלכם", 
                           en="We would love to hear about your limits and preferences"),
                required=True,
                save_to="Registrations",
                order=20,
                options=[
                    QuestionOption(value="yes", text=Text(he="יאאלה", en="Sure")),
                    QuestionOption(value="no", text=Text(he="לא מעוניין לשתף", en="Don't want to share"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            
            # 21 limits_preferences_matrix
            "limits_preferences_matrix": QuestionDefinition(
                question_id="limits_preferences_matrix",
                question_type=QuestionType.MULTI_SELECT,
                title=Text(he="גבולות והעדפות?", en="limits and preferences?"),
                required=True,
                save_to="Users",
                order=21,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            
            # 22 boundaries_text
            "boundaries_text": QuestionDefinition(
                question_id="boundaries_text",
                question_type=QuestionType.TEXT,
                title=Text(he="גבולות - טקסט חופשי", en="Boundaries - free text"),
                required=True,
                save_to="Users",
                order=22,
                placeholder=Text(he=f"תרשמו במילים שלכם\n{skip.he}", en=f"Write in your own words\n{skip.en}"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="share_bdsm_interests", operator="equals", value="no")
                    ]
                )
            ),
            
            # 23 preferences_text
            "preferences_text": QuestionDefinition(
                question_id="preferences_text",
                question_type=QuestionType.TEXT,
                title=Text(he="העדפות - טקסט חופשי", en="Preferences - free text"),
                required=True,
                save_to="Users",
                order=23,
                placeholder=Text(he=f"תרשמו במילים שלכם\n{skip.he}", en=f"Write in your own words\n{skip.en}"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="share_bdsm_interests", operator="equals", value="no")
                    ]
                )
            ),
            
            # 24 bdsm_comments
            "bdsm_comments": QuestionDefinition(
                question_id="bdsm_comments",
                question_type=QuestionType.TEXT,
                title=Text(he="הערות חופשיות בנושא BDSM", en="Anything else you'd like to share?"),
                required=False,
                save_to="Users",
                order=24,
                placeholder=Text(he=f"{skip.he}", en=f"{skip.en}"),
            ),
            
            # 25 food_restrictions
            "food_restrictions": QuestionDefinition(
                question_id="food_restrictions",
                question_type=QuestionType.MULTI_SELECT,
                title=Text(he="האם יש מגבלות אוכל?", en="Are there any food restrictions?"),
                required=True,
                save_to="Users",
                order=25,
                options=[
                    QuestionOption(value="no", text=Text(he="לא", en="No")),
                    QuestionOption(value="vegetarian", text=Text(he="צמחוני", en="Vegetarian")),
                    QuestionOption(value="vegan", text=Text(he="טבעוני", en="Vegan")),
                    QuestionOption(value="kosher", text=Text(he="כשרות", en="Kosher")),
                    QuestionOption(value="allergies", text=Text(he="אלרגיות", en="Allergies")),
                    QuestionOption(value="gluten_free", text=Text(he="ללא גלוט", en="Gluten free")),
                    QuestionOption(value="lactose_free", text=Text(he="ללא לקטוס", en="Lactose free")),
                    QuestionOption(value="other", text=Text(he="אחר", en="Other"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר לפחות אופציה אחת", en="Please select at least one option")
                    )
                ]
            ),
            
            # 26 food_comments
            "food_comments": QuestionDefinition(
                question_id="food_comments",
                question_type=QuestionType.TEXT,
                title=Text(he="אנא פרטו בנושא הגבלות אוכל", en="Please elaborate on the food restrictions"),
                required=False,
                save_to="Users",
                order=26,
                placeholder=Text(he=f"{skip.he}", en=f"{skip.en}"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ]
            ),
            
            # 27 alcohol_in_event
            "alcohol_in_event": QuestionDefinition(
                question_id="alcohol_in_event",
                question_type=QuestionType.SELECT,
                title=Text(he="האם תרצה אלכוהול באירוע (בתוספת תשלום)?", en="Would you like alcohol at the event (with additional payment)?"),
                required=True,
                save_to="Registrations",
                order=27,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="maybe", text=Text(he="אולי", en="Maybe")),
                    QuestionOption(value="no", text=Text(he="לא", en="No")),
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            
            # 28 alcohol_preference
            "alcohol_preference": QuestionDefinition(
                question_id="alcohol_preference",
                question_type=QuestionType.TEXT,
                title=Text(he="מה האלכוהול שלך?", en="What is your alcohol preference?"),
                required=False,
                save_to="Users",
                order=28,
                placeholder=Text(he=f"{skip.he}", en=f"{skip.en}"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="alcohol_in_event", operator="equals", value="no")
                    ]
                )
            ),
            
            # 29 agree_participant_commitment
            "agree_participant_commitment": QuestionDefinition(
                question_id="agree_participant_commitment",
                question_type=QuestionType.SELECT,
                title=Text(he="האם זה מובן?", en="Do you agree to the terms?"),
                required=True,
                save_to="Registrations",
                order=29,
                options=[
                    QuestionOption(value="yes", text=Text(he="הבנתי את הכתוב ומה שמצופה ממני כמשתתפ/ת. אני מסכימ/ה ומאשר/ת", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא הבנתי או אני לא בטוח/ה שהבנתי מה מצופה ממני כמשתתפ/ת באירוע", en="No")),
                    QuestionOption(value="else", text=Text(he="אחר - נחזור אליך כדי לברר", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            
            # 30 enthusiastic_verbal_consent_commitment
            "enthusiastic_verbal_consent_commitment": QuestionDefinition(
                question_id="enthusiastic_verbal_consent_commitment",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם זה ברור שיש לקבל הסכמה מפורשת לכל מגע ואינטראקציה עם אדם אחר?", en="Do you agree to the terms?"),
                required=True,
                save_to="Registrations",
                order=30,
                options=[
                    QuestionOption(value="yes", text=Text(he="ברור בהחלט", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא ברור לי, אשמח להבהרה", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            
            # 31 agree_line_rules
            "agree_line_rules": QuestionDefinition(
                question_id="agree_line_rules",
                question_type=QuestionType.TEXT,
                title=Text(he="האם קראת את חוקי הליין ואתה מאשר אותם?", en="Do you agree to the line rules?"),
                required=True,
                save_to="Registrations",
                order=31,
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא קרא את חוקי הליין היטב ואשר אותם", en="Please read the line rules carefully and agree to them")
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.REGEX,
                        params={"regex": r'זנגביל|ginger'},
                        error_message=Text(he="אנא קרא את חוקי הליין היטב ואשר אותם", en="Please read the line rules carefully and agree to them")
                    )
                ]
            ),
            
            # 32 agree_place_rules  
            "agree_place_rules": QuestionDefinition(
                question_id="agree_place_rules",
                question_type=QuestionType.SELECT,
                title=Text(he="האם קראת את חוקי המקום ואתה מאשר אותם?", en="Do you agree to the place rules?"),
                required=False,
                save_to="Registrations",
                order=32,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            
            # 33 wants_to_helper
            "wants_to_helper": QuestionDefinition(
                question_id="wants_to_helper",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם אתה/את מעוניין/ת לעזור באירוע?", en="Do you want to help at the event?"),
                required=True,
                save_to="Registrations",
                order=33,
                placeholder=Text(he=f'על מנת להרים כזאת הפקה אנו זקוקות לעזרה. אם תוכל ותרצי נשמח שתבואו מוקדם / תשארו לעזור לנו לנקות אחרי בתמורה להנחה בעלות האירוע. הלפרים מקבלים 25% הנחה. ניתן לצבור ע"י בחירת שניהם. ', 
                                en=f"{skip.en}"),
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="maybe", text=Text(he="אולי", en="Maybe")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]   
            ),
            
            # 34 helper_shifts
            "helper_shifts": QuestionDefinition(
                question_id="helper_shifts",
                question_type=QuestionType.SELECT,
                title=Text(he="מתי אתה/את מעוניין/ת לעזור באירוע?", en="When do you want to help at the event?"),
                required=True,
                save_to="Registrations",
                order=34,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="wants_to_helper", operator="equals", value="no")
                    ]
                )
            ),
            
            # 35 is_surtified_DM
            "is_surtified_DM": QuestionDefinition(
                question_id="is_surtified_DM",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם את/ה DM מוסמך?", en="Are you certified to be a DM?"),
                required=True,
                save_to="Users",
                order=35,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            
            # 36 wants_to_DM
            "wants_to_DM": QuestionDefinition(
                question_id="wants_to_DM",
                question_type=QuestionType.BOOLEAN,
                title=Text(he=f"לטובת שמירה מיטבית על המרחב ועל מנת שכולנו נוכל גם להנות, נהיה צוות של דיאמים. DM מקבל כניסה זוגית חינם", 
                                en=f"{skip.en}"),
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="maybe", text=Text(he="אולי", en="Maybe")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="is_surtified_DM", operator="equals", value="no")
                    ]
                )
            ),
            
            # 37 DM_shifts
            "DM_shifts": QuestionDefinition(
                question_id="DM_shifts",
                question_type=QuestionType.MULTI_SELECT,
                title=Text(he="איזה משמרות יכולות להתאים לך?", en="When do you want to be a DM?"),
                required=True,
                save_to="Registrations",
                order=37,
                placeholder=Text(he=f"אשתדל לאפשר לכל אחד את הבחירות שלו.", 
                                en=f"{skip.en}"),
                options=[],  # Will be populated dynamically
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
        }
    
    @staticmethod
    def get_extra_texts() -> Dict[str, Text]:
        """Get extra text for specific questions."""
        return {
            "full_name": Text(
                he="*פרטים אישיים*\nאיזה כיף שאתה מתעניין באירוע! נעבור על כמה שאלות כל מנת להכיר אותך טוב יותר.", 
                en="*Personal details*\nIt's great that you're interested in the event! We'll go through a few questions to get to know you better."
            ),
            "bdsm_experience": Text(
                he='*בואו נדבר בדס"מ*\nנעים מהכיר! היות ומדובר על אירוע בדסמי נעבור כעת על כמה שאלות בנושא.', 
                en="*Let's talk BDSM*\nNice to meet you! Since this is a BDSM event, we'll go through a few questions on the subject."
            ),
            "food_restrictions": Text(
                he="*אוכל ושאר ירקות*", 
                en="*Food, truffles, and trifles*"
            ),
            "agree_participant_commitment": Text(
                he="*חוקים*\n כמעט סוף. בואו נעבור על חוקי הליין, המקום וכו'.", 
                en="*Rules*\n Almost done. Let's go through the line rules, the place, and so on."
            ),
            "wants_to_helper": Text(
                he="*הלפרים ו DM-ים*\nזהו! סיימנו, אך לפני שאני משחרר אתכם, אשמח לדעת האם תרצו לעזור באירוע (בתמורה להנחה בעלות האירוע)", 
                en="*Helpers and DMs*\nThat's it! We're done, but before I let you go, I'd like to know if you'd like to help at the event (in exchange for a discount on the event's cost)"
            ),
            "wants_to_DM": Text(
                he=f"לטובת שמירה מיטבית על המרחב ועל מנת שכולנו נוכל גם להנות, נהיה צוות של דיאמים. DM מקבל כניסה זוגית חינם", 
                en=f"We will have a team of DMs to preserve the safety of the space and everyone in it so that we can all enjoy ourselves. DM gets a free pair entry"
            ),
            "completion": Text(
                he="תודה שנרשמת לאירוע! ניתן להתחיל מחדש בכל עת עם הפקודה /start", 
                en="Thank you for filling out the form! You can start over at any time with the /start command"
            )
        }
    
    @staticmethod
    def get_form_metadata() -> Dict[str, Any]:
        """Get form metadata and configuration."""
        return {
            "total_questions": 37,
            "supported_languages": ["he", "en"],
            "default_language": "he",
            "form_name": "Wild Ginger Event Registration",
            "form_version": "1.0.0",
            "description": {
                "he": "טופס הרשמה לאירועי Wild Ginger",
                "en": "Wild Ginger Event Registration Form"
            },
            "contact_info": {
                "he": "לשאלות נוספות: @wildginger_admin",
                "en": "For questions: @wildginger_admin"
            }
        } 