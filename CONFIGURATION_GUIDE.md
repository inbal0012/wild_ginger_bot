# Form Configuration Guide

This guide explains how to customize the event registration form system for your specific needs. The system is designed to be highly configurable, allowing you to create custom forms without touching any Python code.

## Overview

The form system supports two configuration approaches:

1. **Python Class-based Configuration** - For developers who want to modify the form structure programmatically
2. **JSON File-based Configuration** - For non-technical users who want to customize forms through simple text files

## Quick Start

### For Non-Technical Users (JSON Configuration)

1. **Copy the template configuration file:**
   ```bash
   cp telegram_bot/config/form_config.json my_event_config.json
   ```

2. **Edit the JSON file** with your event details:
   ```json
   {
     "form_metadata": {
       "form_name": "My Awesome Event Registration",
       "form_version": "1.0.0",
       "total_questions": 15,
       "supported_languages": ["en", "es"],
       "default_language": "en",
       "description": {
         "en": "Registration form for My Awesome Event",
         "es": "Formulario de registro para Mi Evento Increíble"
       }
     }
   }
   ```

3. **Update the bot initialization** to use your config:
   ```python
   # In your main bot file
   form_flow_service = FormFlowService(sheets_service, config_source="json")
   ```

### For Developers (Python Configuration)

1. **Create a custom configuration class:**
   ```python
   # my_event_config.py
   from telegram_bot.config.form_config import FormConfig
   from telegram_bot.models.form_flow import QuestionDefinition, QuestionType, Text, ValidationRule, ValidationRuleType
   
   class MyEventConfig(FormConfig):
       @staticmethod
       def get_question_definitions():
           return {
               "language": QuestionDefinition(
                   question_id="language",
                   question_type=QuestionType.SELECT,
                   title=Text(
                       en="What language would you prefer?",
                       es="¿Qué idioma prefieres?"
                   ),
                   required=True,
                   save_to="Users",
                   order=1,
                   options=[
                       QuestionOption(value="en", text=Text(en="English", es="Inglés")),
                       QuestionOption(value="es", text=Text(en="Spanish", es="Español"))
                   ]
               ),
               # Add more questions...
           }
   ```

2. **Use your custom configuration:**
   ```python
   from my_event_config import MyEventConfig
   
   # Update the FormConfigLoader to use your class
   form_flow_service = FormFlowService(sheets_service, config_source="python")
   ```

## Configuration Structure

### Form Metadata

```json
{
  "form_metadata": {
    "form_name": "Event Name",
    "form_version": "1.0.0",
    "total_questions": 20,
    "supported_languages": ["en", "es", "fr"],
    "default_language": "en",
    "description": {
      "en": "Event description in English",
      "es": "Descripción del evento en español"
    },
    "contact_info": {
      "en": "Contact: @event_admin",
      "es": "Contacto: @event_admin"
    }
  }
}
```

### Question Definitions

Each question has the following structure:

```json
{
  "question_id": "unique_question_id",
  "question_type": "TEXT|SELECT|MULTI_SELECT|BOOLEAN|DATE|TELEGRAM_LINK|FACEBOOK_LINK",
  "title": {
    "en": "Question title in English",
    "es": "Título de la pregunta en español"
  },
  "required": true,
  "save_to": "Users|Registrations",
  "order": 1,
  "placeholder": {
    "en": "Placeholder text in English",
    "es": "Texto de placeholder en español"
  },
  "options": [
    {
      "value": "option_value",
      "text": {
        "en": "Option text in English",
        "es": "Texto de opción en español"
      }
    }
  ],
  "validation_rules": [
    {
      "rule_type": "REQUIRED|MIN_LENGTH|MAX_LENGTH|REGEX|TELEGRAM_LINK|FACEBOOK_LINK|DATE_RANGE|AGE_RANGE",
      "params": {
        "min": 2,
        "max": 100,
        "regex": "pattern",
        "min_age": 18,
        "max_age": 100
      },
      "error_message": {
        "en": "Error message in English",
        "es": "Mensaje de error en español"
      }
    }
  ],
  "skip_condition": {
    "operator": "OR|AND|NOT",
    "conditions": [
      {
        "type": "field_value|user_exists|event_type",
        "operator": "equals|not_equals|in|not_in",
        "field": "field_name",
        "value": "expected_value"
      }
    ]
  }
}
```

### Question Types

1. **TEXT** - Free text input
2. **SELECT** - Single choice from options
3. **MULTI_SELECT** - Multiple choices from options
4. **BOOLEAN** - Yes/No question
5. **DATE** - Date input (DD/MM/YYYY format)
6. **TELEGRAM_LINK** - Telegram username or link
7. **FACEBOOK_LINK** - Facebook or Instagram profile link

### Validation Rules

1. **REQUIRED** - Field must not be empty
2. **MIN_LENGTH** - Minimum text length
3. **MAX_LENGTH** - Maximum text length
4. **REGEX** - Regular expression pattern matching
5. **TELEGRAM_LINK** - Valid Telegram link format
6. **FACEBOOK_LINK** - Valid Facebook/Instagram link format
7. **DATE_RANGE** - Valid date format
8. **AGE_RANGE** - Age validation from birth date

### Skip Conditions

Skip conditions allow you to show/hide questions based on previous answers:

1. **field_value** - Skip based on a previous field's value
2. **user_exists** - Skip if user already exists in the system
3. **event_type** - Skip based on event type

### Extra Texts

Extra texts are sent before specific questions to provide context:

```json
{
  "extra_texts": {
    "full_name": {
      "en": "*Personal Details*\nLet's start with some basic information about you.",
      "es": "*Detalles Personales*\nComencemos con información básica sobre ti."
    },
    "completion": {
      "en": "Thank you for registering! We'll contact you soon.",
      "es": "¡Gracias por registrarte! Te contactaremos pronto."
    }
  }
}
```

## Examples

### Simple Contact Form

```json
{
  "form_metadata": {
    "form_name": "Contact Form",
    "form_version": "1.0.0",
    "total_questions": 3,
    "supported_languages": ["en"],
    "default_language": "en"
  },
  "questions": {
    "name": {
      "question_id": "name",
      "question_type": "TEXT",
      "title": {
        "en": "What's your name?"
      },
      "required": true,
      "save_to": "Users",
      "order": 1,
      "validation_rules": [
        {
          "rule_type": "REQUIRED",
          "error_message": {
            "en": "Please enter your name"
          }
        },
        {
          "rule_type": "MIN_LENGTH",
          "params": {
            "min": 2
          },
          "error_message": {
            "en": "Name must be at least 2 characters"
          }
        }
      ]
    },
    "email": {
      "question_id": "email",
      "question_type": "TEXT",
      "title": {
        "en": "What's your email address?"
      },
      "required": true,
      "save_to": "Users",
      "order": 2,
      "validation_rules": [
        {
          "rule_type": "REGEX",
          "params": {
            "regex": "^[^@]+@[^@]+\\.[^@]+$"
          },
          "error_message": {
            "en": "Please enter a valid email address"
          }
        }
      ]
    },
    "message": {
      "question_id": "message",
      "question_type": "TEXT",
      "title": {
        "en": "What's your message?"
      },
      "required": false,
      "save_to": "Users",
      "order": 3,
      "validation_rules": [
        {
          "rule_type": "MAX_LENGTH",
          "params": {
            "max": 500
          },
          "error_message": {
            "en": "Message must be less than 500 characters"
          }
        }
      ]
    }
  }
}
```

### Event Registration with Conditional Questions

```json
{
  "form_metadata": {
    "form_name": "Conference Registration",
    "form_version": "1.0.0",
    "total_questions": 5,
    "supported_languages": ["en"],
    "default_language": "en"
  },
  "questions": {
    "language": {
      "question_id": "language",
      "question_type": "SELECT",
      "title": {
        "en": "What language would you prefer?"
      },
      "required": true,
      "save_to": "Users",
      "order": 1,
      "options": [
        {
          "value": "en",
          "text": {
            "en": "English"
          }
        },
        {
          "value": "es",
          "text": {
            "en": "Spanish"
          }
        }
      ]
    },
    "registration_type": {
      "question_id": "registration_type",
      "question_type": "SELECT",
      "title": {
        "en": "What type of registration do you need?"
      },
      "required": true,
      "save_to": "Registrations",
      "order": 2,
      "options": [
        {
          "value": "attendee",
          "text": {
            "en": "Attendee"
          }
        },
        {
          "value": "speaker",
          "text": {
            "en": "Speaker"
          }
        },
        {
          "value": "volunteer",
          "text": {
            "en": "Volunteer"
          }
        }
      ]
    },
    "presentation_topic": {
      "question_id": "presentation_topic",
      "question_type": "TEXT",
      "title": {
        "en": "What's your presentation topic?"
      },
      "required": true,
      "save_to": "Registrations",
      "order": 3,
      "skip_condition": {
        "operator": "OR",
        "conditions": [
          {
            "type": "field_value",
            "field": "registration_type",
            "operator": "equals",
            "value": "speaker"
          }
        ]
      }
    },
    "volunteer_shift": {
      "question_id": "volunteer_shift",
      "question_type": "SELECT",
      "title": {
        "en": "Which shift would you like to volunteer for?"
      },
      "required": true,
      "save_to": "Registrations",
      "order": 4,
      "options": [
        {
          "value": "morning",
          "text": {
            "en": "Morning (9 AM - 12 PM)"
          }
        },
        {
          "value": "afternoon",
          "text": {
            "en": "Afternoon (1 PM - 4 PM)"
          }
        },
        {
          "value": "evening",
          "text": {
            "en": "Evening (5 PM - 8 PM)"
          }
        }
      ],
      "skip_condition": {
        "operator": "OR",
        "conditions": [
          {
            "type": "field_value",
            "field": "registration_type",
            "operator": "equals",
            "value": "volunteer"
          }
        ]
      }
    },
    "dietary_restrictions": {
      "question_id": "dietary_restrictions",
      "question_type": "MULTI_SELECT",
      "title": {
        "en": "Do you have any dietary restrictions?"
      },
      "required": false,
      "save_to": "Users",
      "order": 5,
      "options": [
        {
          "value": "none",
          "text": {
            "en": "None"
          }
        },
        {
          "value": "vegetarian",
          "text": {
            "en": "Vegetarian"
          }
        },
        {
          "value": "vegan",
          "text": {
            "en": "Vegan"
          }
        },
        {
          "value": "gluten_free",
          "text": {
            "en": "Gluten-free"
          }
        },
        {
          "value": "other",
          "text": {
            "en": "Other"
          }
        }
      ]
    }
  }
}
```

## Advanced Features

### Dynamic Options

For questions that need dynamic options (like event lists), you can leave the options array empty in the JSON config and populate it programmatically:

```json
{
  "event_selection": {
    "question_id": "event_selection",
    "question_type": "SELECT",
    "title": {
      "en": "Which event would you like to attend?"
    },
    "required": true,
    "save_to": "Registrations",
    "order": 3,
    "options": []
  }
}
```

The system will automatically populate this with available events from your database.

### Custom Validation

You can add custom validation by extending the validation system:

```python
# In your custom configuration
class CustomValidationRule(ValidationRule):
    def validate(self, value, form_state):
        # Custom validation logic
        if self.rule_type == ValidationRuleType.CUSTOM:
            return self.custom_validate(value, form_state)
        return super().validate(value, form_state)
    
    def custom_validate(self, value, form_state):
        # Your custom validation logic here
        pass
```

### Multi-language Support

The system supports multiple languages. Simply add translations for all text fields:

```json
{
  "title": {
    "en": "What's your name?",
    "es": "¿Cuál es tu nombre?",
    "fr": "Quel est votre nom?",
    "de": "Wie ist Ihr Name?"
  }
}
```

## Best Practices

1. **Question Ordering**: Always use sequential order numbers (1, 2, 3, etc.)
2. **Validation**: Provide clear, user-friendly error messages
3. **Skip Conditions**: Test skip conditions thoroughly to ensure questions appear/disappear correctly
4. **Multi-language**: Provide translations for all supported languages
5. **Testing**: Test your configuration with various user scenarios
6. **Backup**: Keep backups of your configuration files
7. **Version Control**: Use version control for your configuration files

## Troubleshooting

### Common Issues

1. **Questions not appearing**: Check skip conditions and field dependencies
2. **Validation errors**: Ensure validation rules are properly formatted
3. **Language issues**: Verify all required languages have translations
4. **Order problems**: Check that question order numbers are sequential

### Debug Mode

Enable debug mode to see detailed information about form processing:

```python
# In your bot initialization
form_flow_service = FormFlowService(sheets_service, config_source="json")
form_flow_service.debug_mode = True
```

### Configuration Validation

The system automatically validates your configuration on startup. Check the logs for any validation errors or warnings.

## Support

For help with configuration:

1. Check the examples in this guide
2. Review the validation logs for specific errors
3. Test with a simple configuration first
4. Contact support with your specific use case

## Migration from Hardcoded Forms

If you're migrating from the old hardcoded form system:

1. Export your current form structure to JSON using the configuration loader
2. Review and modify the exported JSON
3. Test the new configuration thoroughly
4. Update your bot initialization to use the new configuration system

The system is designed to be backward compatible, so you can gradually migrate your forms. 