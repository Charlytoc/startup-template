export interface paths {
    "/api/auth/organizations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Organizations
         * @description Get list of available organizations for signup
         */
        get: operations["core_routers_auth_list_organizations"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/signup": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Signup
         * @description Register a new user
         */
        post: operations["core_routers_auth_signup"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Login
         * @description Authenticate user and return API token
         */
        post: operations["core_routers_auth_login"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Current User
         * @description Get current authenticated user
         */
        get: operations["core_routers_auth_get_current_user"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/tokens": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List User Tokens
         * @description List user's API tokens
         */
        get: operations["core_routers_auth_list_user_tokens"];
        put?: never;
        /**
         * Create Api Token
         * @description Create a new API token for the user
         */
        post: operations["core_routers_auth_create_api_token"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/tokens/{token_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /**
         * Revoke Api Token
         * @description Revoke an API token
         */
        delete: operations["core_routers_auth_revoke_api_token"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Logout
         * @description Logout user (for both session and API token auth)
         */
        post: operations["core_routers_auth_logout"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/change-password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Change Password
         * @description Change user password
         */
        post: operations["core_routers_auth_change_password"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/profile": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get User Profile
         * @description Get current user's profile
         */
        get: operations["core_routers_user_profile_get_user_profile"];
        /**
         * Update User Profile
         * @description Update existing user profile
         */
        put: operations["core_routers_user_profile_update_user_profile"];
        /**
         * Create User Profile
         * @description Create or update user profile
         */
        post: operations["core_routers_user_profile_create_user_profile"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/profile/learning-context": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Learning Context
         * @description Get user's learning context for AI personalization
         */
        get: operations["core_routers_user_profile_get_learning_context"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/native-languages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Native Languages
         * @description Get list of available native languages
         */
        get: operations["core_routers_languages_get_native_languages"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/languages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Languages
         * @description Get list of available languages for learning
         */
        get: operations["core_routers_languages_get_languages"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/languages/{language_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Language
         * @description Get specific language details
         */
        get: operations["core_routers_languages_get_language"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/languages/{language_id}/paths": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Language Paths
         * @description Get language paths for a specific language
         */
        get: operations["core_routers_languages_get_language_paths"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/languages/{language_id}/current-path": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Current Language Path
         * @description Get the current active language path for a language
         */
        get: operations["core_routers_languages_get_current_language_path"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/learning-languages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get User Learning Languages
         * @description Get current user's learning languages
         */
        get: operations["core_routers_learning_language_get_user_learning_languages"];
        put?: never;
        /**
         * Create Learning Language
         * @description Create a new learning language for the user
         */
        post: operations["core_routers_learning_language_create_learning_language"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/learning-languages/{learning_language_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /**
         * Update Learning Language
         * @description Update an existing learning language
         */
        put: operations["core_routers_learning_language_update_learning_language"];
        post?: never;
        /**
         * Delete Learning Language
         * @description Delete (deactivate) a learning language
         */
        delete: operations["core_routers_learning_language_delete_learning_language"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/learning-languages/{learning_language_id}/update-progress": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Update Learning Progress
         * @description Update learning progress for a language
         */
        post: operations["core_routers_learning_language_update_learning_progress"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/config/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get App Config
         * @description Get public application configuration.
         *     Returns key-value pairs of active configurations.
         */
        get: operations["core_routers_config_get_app_config"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/config/theme/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Theme Config
         * @description Get theme-related configuration specifically.
         *     Returns default theme and available themes.
         */
        get: operations["core_routers_config_get_theme_config"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/lessons/{lesson_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Lesson */
        get: operations["core_routers_lessons_get_lesson"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/lessons/{lesson_id}/messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Send Lesson Message */
        post: operations["core_routers_lessons_send_lesson_message"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/language-path/{path_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Language Path */
        get: operations["core_routers_modules_get_language_path"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/module/{module_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Module Lessons */
        get: operations["core_routers_modules_get_module_lessons"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/themes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Themes
         * @description Get all active themes available for selection.
         */
        get: operations["core_routers_themes_list_themes"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/themes/{theme_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Theme
         * @description Get a specific theme by ID.
         */
        get: operations["core_routers_themes_get_theme"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/themes/default": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Default Theme
         * @description Get the default theme.
         */
        get: operations["core_routers_themes_get_default_theme"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** OrganizationResponse */
        OrganizationResponse: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Domain */
            domain: string;
            /** Status */
            status: string;
        };
        /** AuthResponse */
        AuthResponse: {
            /** Api Token */
            api_token: string;
            user: components["schemas"]["UserResponse"];
            organization: components["schemas"]["OrganizationResponse"];
        };
        /** UserResponse */
        UserResponse: {
            /** Id */
            id: number;
            /** Email */
            email: string;
            /** First Name */
            first_name: string | null;
            /** Last Name */
            last_name: string | null;
            /** Organization */
            organization: {
                [key: string]: unknown;
            };
            /** Profile */
            profile: {
                [key: string]: unknown;
            } | null;
            /** Profile Picture */
            profile_picture: string | null;
            /** Is Active */
            is_active: boolean;
            /** Is Staff */
            is_staff: boolean;
            /** Created */
            created: string;
        };
        /** ErrorResponseSchema */
        ErrorResponseSchema: {
            /** Error */
            error: string;
            /** Error Code */
            error_code: string;
        };
        /** SignupRequest */
        SignupRequest: {
            /** Email */
            email: string;
            /** Password */
            password: string;
            /** First Name */
            first_name?: string | null;
            /** Last Name */
            last_name?: string | null;
            /** Organization Id */
            organization_id?: number | null;
        };
        /** LoginRequest */
        LoginRequest: {
            /** Email */
            email: string;
            /** Password */
            password: string;
        };
        /** ApiTokenResponse */
        ApiTokenResponse: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Token Preview */
            token_preview: string;
            /** Is Active */
            is_active: boolean;
            /** Expires At */
            expires_at: string | null;
            /** Last Used At */
            last_used_at: string | null;
            /** Created */
            created: string;
        };
        /** UserProfileResponse */
        UserProfileResponse: {
            /** Id */
            id: number;
            /** Native Language */
            native_language: string;
            /** Date Of Birth */
            date_of_birth?: string | null;
            /** Age */
            age?: number | null;
            /** Profession */
            profession?: string | null;
            /** Description */
            description?: string | null;
            /** Daily Learning Time */
            daily_learning_time?: number | null;
            /** Timezone */
            timezone?: string | null;
            /** Ai Personality Profile */
            ai_personality_profile?: {
                [key: string]: unknown;
            } | null;
            /** Created */
            created: string;
            /** Modified */
            modified: string;
        };
        /** UserProfileUpdateRequest */
        UserProfileUpdateRequest: {
            /** Native Language */
            native_language?: string | null;
            /** Date Of Birth */
            date_of_birth?: string | null;
            /** Profession */
            profession?: string | null;
            /** Description */
            description?: string | null;
            /** Daily Learning Time */
            daily_learning_time?: number | null;
            /** Timezone */
            timezone?: string | null;
            /** Ai Personality Profile */
            ai_personality_profile?: {
                [key: string]: unknown;
            } | null;
        };
        /** NativeLanguageResponse */
        NativeLanguageResponse: {
            /** Code */
            code: string;
            /** Name */
            name: string;
            /** Native Name */
            native_name: string;
            /** Flag Emoji */
            flag_emoji: string;
        };
        /** LanguageResponse */
        LanguageResponse: {
            /** Id */
            id: number;
            /** Code */
            code: string;
            /** Name */
            name: string;
            /** Native Name */
            native_name: string;
            /** Description */
            description: string;
            /** Is Active */
            is_active: boolean;
            /** Total Levels */
            total_levels: number;
            /** Created */
            created: string;
        };
        /** LanguagePathResponse */
        LanguagePathResponse: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Description */
            description: string;
            /** Modules */
            modules: components["schemas"]["ModuleResponse"][];
        };
        /** LearningLanguageResponse */
        LearningLanguageResponse: {
            /** Id */
            id: number;
            /** User Id */
            user_id: number;
            /** Language Id */
            language_id: number;
            /** Language Name */
            language_name: string;
            /** Language Code */
            language_code: string;
            /** Country Code */
            country_code: string;
            /** Language Path Id */
            language_path_id: number;
            /** Reason For Learning */
            reason_for_learning: string;
            /** Current Level */
            current_level: string;
            /** Target Level */
            target_level: string;
            /** Hours Per Week */
            hours_per_week: number;
            /** Preferred Learning Times */
            preferred_learning_times: string[];
            /** Total Hours Studied */
            total_hours_studied: number;
            /** Last Study Date */
            last_study_date: string | null;
            /** Is Active */
            is_active: boolean;
            /** Is Primary */
            is_primary: boolean;
            /** Progress Percentage */
            progress_percentage: number;
            /** Estimated Weeks To Target */
            estimated_weeks_to_target: number | null;
            /** Created */
            created: string;
            /** Modified */
            modified: string;
        };
        /** LearningLanguageCreateRequest */
        LearningLanguageCreateRequest: {
            /** Language Id */
            language_id: number;
            /** Reason For Learning */
            reason_for_learning: string;
            /**
             * Current Level
             * @default A1
             */
            current_level: string;
            /**
             * Target Level
             * @default B2
             */
            target_level: string;
            /**
             * Hours Per Week
             * @default 5
             */
            hours_per_week: number;
            /**
             * Preferred Learning Times
             * @default [
             *       "morning",
             *       "evening"
             *     ]
             */
            preferred_learning_times: string[];
        };
        /** LearningLanguageUpdateRequest */
        LearningLanguageUpdateRequest: {
            /** Reason For Learning */
            reason_for_learning?: string | null;
            /** Current Level */
            current_level?: string | null;
            /** Target Level */
            target_level?: string | null;
            /** Hours Per Week */
            hours_per_week?: number | null;
            /** Preferred Learning Times */
            preferred_learning_times?: string[] | null;
            /** Is Active */
            is_active?: boolean | null;
            /** Is Primary */
            is_primary?: boolean | null;
        };
        /** AppConfigResponse */
        AppConfigResponse: {
            /** Success */
            success: boolean;
            /** Data */
            data: {
                [key: string]: string;
            };
            /** Message */
            message: string;
        };
        /** ThemeConfigResponse */
        ThemeConfigResponse: {
            /** Success */
            success: boolean;
            data: components["schemas"]["ThemeData"];
            /** Message */
            message: string;
        };
        /** ThemeData */
        ThemeData: {
            /** Default Theme Key */
            default_theme_key: string;
            /** Available Themes */
            available_themes: string[];
        };
        /** ExchangeMessage */
        ExchangeMessage: {
            /**
             * Id
             * @description Message ID
             */
            id?: number | null;
            /**
             * Type
             * @default text
             * @enum {string}
             */
            type: "text" | "file";
            /**
             * Role
             * @default user
             * @enum {string}
             */
            role: "user" | "assistant";
            /**
             * Content
             * @description Content of the message
             * @default
             */
            content: string | {
                [key: string]: unknown;
            };
            /**
             * Created
             * @description Creation timestamp
             */
            created?: string | null;
        };
        /** LessonResponse */
        LessonResponse: {
            /** Id */
            id: number;
            /** Title */
            title: string;
            /** Description */
            description: string;
            /** Status */
            status: string;
            /** Started At */
            started_at?: string | null;
            /** Completed At */
            completed_at?: string | null;
            /** Module Id */
            module_id?: number | null;
            /** Welcome Message */
            welcome_message: string;
            /** Summary */
            summary?: {
                [key: string]: unknown;
            } | null;
            /**
             * Messages
             * @default []
             */
            messages: components["schemas"]["ExchangeMessage"][];
        };
        /** MessageResponse */
        MessageResponse: {
            /** Status */
            status: string;
            /** Lesson Id */
            lesson_id: number;
        };
        /** MessageRequest */
        MessageRequest: {
            /** Message */
            message: string;
        };
        /** ModuleResponse */
        ModuleResponse: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Description */
            description: string;
            /** Order */
            order: number;
            /** Estimated Hours */
            estimated_hours: number;
            /** Is Active */
            is_active: boolean;
            /** Language Level */
            language_level: string;
            /** Skills */
            skills: components["schemas"]["SkillResponse"][];
        };
        /** SkillResponse */
        SkillResponse: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Skill Type */
            skill_type: string;
            /** Difficulty */
            difficulty: number;
            /** Estimated Duration Hours */
            estimated_duration_hours: number;
        };
        /** ModuleDetailResponse */
        ModuleDetailResponse: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Description */
            description: string;
            /** Order */
            order: number;
            /** Estimated Hours */
            estimated_hours: number;
            /** Lessons */
            lessons: components["schemas"]["LessonResponse"][];
        };
        /**
         * ThemeResponse
         * @description Response schema for theme data.
         */
        ThemeResponse: {
            /** Id */
            id: string;
            /** Name */
            name: string;
            /** Description */
            description: string;
            /** Light Colors */
            light_colors: {
                [key: string]: unknown;
            };
            /** Dark Colors */
            dark_colors: {
                [key: string]: unknown;
            };
            /** Is Active */
            is_active: boolean;
            /** Is Default */
            is_default: boolean;
            /** Created At */
            created_at: string;
            /** Updated At */
            updated_at: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    core_routers_auth_list_organizations: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OrganizationResponse"][];
                };
            };
        };
    };
    core_routers_auth_signup: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SignupRequest"];
            };
        };
        responses: {
            /** @description Created */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_auth_login: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginRequest"];
            };
        };
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_auth_get_current_user: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_auth_list_user_tokens: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiTokenResponse"][];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_auth_create_api_token: {
        parameters: {
            query: {
                name: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Created */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiTokenResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_auth_revoke_api_token: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                token_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_auth_logout: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_auth_change_password: {
        parameters: {
            query: {
                current_password: string;
                new_password: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_user_profile_get_user_profile: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserProfileResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_user_profile_update_user_profile: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UserProfileUpdateRequest"];
            };
        };
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserProfileResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_user_profile_create_user_profile: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UserProfileUpdateRequest"];
            };
        };
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserProfileResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_user_profile_get_learning_context: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_languages_get_native_languages: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NativeLanguageResponse"][];
                };
            };
        };
    };
    core_routers_languages_get_languages: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LanguageResponse"][];
                };
            };
        };
    };
    core_routers_languages_get_language: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                language_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LanguageResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_languages_get_language_paths: {
        parameters: {
            query?: {
                active_only?: boolean;
            };
            header?: never;
            path: {
                language_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LanguagePathResponse"][];
                };
            };
        };
    };
    core_routers_languages_get_current_language_path: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                language_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LanguagePathResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_learning_language_get_user_learning_languages: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LearningLanguageResponse"][];
                };
            };
        };
    };
    core_routers_learning_language_create_learning_language: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LearningLanguageCreateRequest"];
            };
        };
        responses: {
            /** @description Created */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LearningLanguageResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_learning_language_update_learning_language: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                learning_language_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LearningLanguageUpdateRequest"];
            };
        };
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LearningLanguageResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_learning_language_delete_learning_language: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                learning_language_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_learning_language_update_learning_progress: {
        parameters: {
            query: {
                hours_studied: number;
                new_level?: string | null;
            };
            header?: never;
            path: {
                learning_language_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LearningLanguageResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponseSchema"];
                };
            };
        };
    };
    core_routers_config_get_app_config: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AppConfigResponse"];
                };
            };
        };
    };
    core_routers_config_get_theme_config: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ThemeConfigResponse"];
                };
            };
        };
    };
    core_routers_lessons_get_lesson: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lesson_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LessonResponse"];
                };
            };
        };
    };
    core_routers_lessons_send_lesson_message: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lesson_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MessageRequest"];
            };
        };
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
        };
    };
    core_routers_modules_get_language_path: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                path_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LanguagePathResponse"];
                };
            };
        };
    };
    core_routers_modules_get_module_lessons: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                module_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ModuleDetailResponse"];
                };
            };
        };
    };
    core_routers_themes_list_themes: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ThemeResponse"][];
                };
            };
        };
    };
    core_routers_themes_get_theme: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                theme_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ThemeResponse"];
                };
            };
        };
    };
    core_routers_themes_get_default_theme: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ThemeResponse"];
                };
            };
        };
    };
}
