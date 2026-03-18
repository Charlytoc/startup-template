# Django Management Commands

## setup_language

Creates a comprehensive language configuration in the database with complete learning paths, levels, and skills.

### Usage

```bash
# Using taskfile (recommended)
./taskfile.sh run setup_language <language_code> [options]

# Direct Django command
docker-compose exec web python manage.py setup_language <language_code> [options]
```

### Examples

```bash
# Set up Spanish language configuration
./taskfile.sh run setup_language es

# Set up French with custom name
./taskfile.sh run setup_language fr --name "French" --native-name "Français"

# Force recreation of existing language
./taskfile.sh run setup_language en --force

# Dry run to see what would be created
./taskfile.sh run setup_language de --dry-run
```

### Supported Languages

The command automatically recognizes these language codes:

- `en` - English
- `es` - Spanish (Español)
- `fr` - French (Français)
- `de` - German (Deutsch)
- `it` - Italian (Italiano)
- `pt` - Portuguese (Português)
- `ru` - Russian (Русский)
- `ja` - Japanese (日本語)
- `ko` - Korean (한국어)
- `zh` - Chinese (中文)

### What Gets Created

For each language, the command creates:

1. **Language** - Basic language information
2. **LanguagePath** - Learning path with versioning
3. **LanguageLevel** - All 6 CEFR levels (A1-C2)
4. **Skills** - ~120 skills across all levels and skill types

### Skill Types Created

- **Grammar** - Tenses, structures, syntax
- **Vocabulary** - Words, phrases, expressions
- **Pronunciation** - Sounds, accent, rhythm
- **Listening** - Comprehension, audio skills
- **Speaking** - Conversation, fluency
- **Reading** - Text comprehension, analysis
- **Writing** - Composition, formal writing
- **Pragmatics** - Social context, appropriateness
- **Cultural** - Cultural awareness, customs
- **Metacognitive** - Learning strategies, study skills

### Command Options

- `language_code` (required) - Two-letter language code
- `--name` - Language name in English
- `--native-name` - Native language name
- `--description` - Custom description
- `--force` - Force recreation if language exists
- `--dry-run` - Show what would be created without creating

### Database Structure

```
Language
└── LanguagePath (v1)
    ├── LanguageLevel (A1)
    │   └── Skills (20 skills)
    ├── LanguageLevel (A2)
    │   └── Skills (20 skills)
    ├── LanguageLevel (B1)
    │   └── Skills (20 skills)
    ├── LanguageLevel (B2)
    │   └── Skills (20 skills)
    ├── LanguageLevel (C1)
    │   └── Skills (20 skills)
    └── LanguageLevel (C2)
        └── Skills (20 skills)
```

### Learning Path Features

Each level includes:

- **Modules** - Organized learning units
- **Activities** - Specific exercises and tasks
- **Assessment Criteria** - Evaluation standards
- **Suggested Resources** - Learning materials
- **Can-do Descriptors** - Learning objectives

### Time Estimates

- **A1**: ~40 hours (Beginner)
- **A2**: ~60 hours (Elementary)
- **B1**: ~80 hours (Intermediate)
- **B2**: ~100 hours (Upper Intermediate)
- **C1**: ~120 hours (Advanced)
- **C2**: ~150 hours (Proficient)

**Total**: ~550 hours for complete language mastery

### Skill Properties

Each skill includes:

- **Difficulty** (1-5 scale)
- **Duration** (estimated hours)
- **Domain Threshold** (mastery percentage)
- **Decay Rate** (forgetting curve)
- **Practice Frequency** (spaced repetition)
- **Learning Objectives** (specific goals)
- **Prerequisites** (skill dependencies)

This comprehensive setup enables:

- Adaptive learning algorithms
- Spaced repetition systems
- Progress tracking
- Personalized learning paths
- Skill mastery assessment
- Learning analytics
