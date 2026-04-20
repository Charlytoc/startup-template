export interface paths {
    "/api/auth/organizations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Organizations */
        get: operations["core_routers_auth_list_organizations"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/my-organizations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List My Organizations */
        get: operations["core_routers_auth_list_my_organizations"];
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
        /** Signup */
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
        /** Login */
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
        /** Get Current User */
        get: operations["core_routers_auth_get_current_user"];
        put?: never;
        post?: never;
        delete?: never;
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
        /** Logout */
        post: operations["core_routers_auth_logout"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/agentic-chat/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["core_routers_agentic_chat_health"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/agentic-chat/messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Send Message */
        post: operations["core_routers_agentic_chat_send_message"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/workspaces/{workspace_id}/integrations/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Workspace Integrations */
        get: operations["core_routers_workspaces_list_workspace_integrations"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/workspaces/{workspace_id}/integrations/{integration_account_id}/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Workspace Integration */
        get: operations["core_routers_workspaces_get_workspace_integration"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/workspaces/{workspace_id}/integrations/{integration_account_id}/task-executions/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Integration Task Executions */
        get: operations["core_routers_workspaces_list_integration_task_executions"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/workspaces/{workspace_id}/integrations/{integration_account_id}/conversations/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Integration Conversations */
        get: operations["core_routers_workspaces_list_integration_conversations"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/workspaces/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Workspaces */
        get: operations["core_routers_workspaces_list_workspaces"];
        put?: never;
        /** Create Workspace */
        post: operations["core_routers_workspaces_create_workspace"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/workspaces/{workspace_id}/cyber-identities/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Cyber Identities */
        get: operations["core_routers_workspaces_list_cyber_identities"];
        put?: never;
        /** Create Cyber Identity */
        post: operations["core_routers_workspaces_create_cyber_identity"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/workspaces/{workspace_id}/cyber-identities/{cyber_identity_id}/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Cyber Identity */
        delete: operations["core_routers_workspaces_delete_cyber_identity"];
        options?: never;
        head?: never;
        /** Update Cyber Identity */
        patch: operations["core_routers_workspaces_update_cyber_identity"];
        trace?: never;
    };
    "/api/workspaces/{workspace_id}/actionables/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Workspace Actionables */
        get: operations["core_routers_workspaces_list_workspace_actionables"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/workspaces/{workspace_id}/job-assignments/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Job Assignments */
        get: operations["core_routers_workspaces_list_job_assignments"];
        put?: never;
        /** Create Job Assignment */
        post: operations["core_routers_workspaces_create_job_assignment"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/workspaces/{workspace_id}/job-assignments/{job_assignment_id}/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Job Assignment */
        delete: operations["core_routers_workspaces_delete_job_assignment"];
        options?: never;
        head?: never;
        /** Update Job Assignment */
        patch: operations["core_routers_workspaces_update_job_assignment"];
        trace?: never;
    };
    "/api/integrations/telegram/webhook/{webhook_path_token}/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Telegram Webhook */
        post: operations["core_routers_integrations_telegram_telegram_webhook"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/integrations/telegram/workspaces/{workspace_id}/telegram/connect": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Telegram Connect */
        post: operations["core_routers_integrations_telegram_telegram_connect"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/integrations/telegram/workspaces/{workspace_id}/telegram/approve-sender": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Telegram Approve Sender */
        post: operations["core_routers_integrations_telegram_telegram_approve_sender"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/integrations/telegram/workspaces/{workspace_id}/telegram/{integration_account_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Telegram Disconnect */
        delete: operations["core_routers_integrations_telegram_telegram_disconnect"];
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
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Domain */
            domain: string;
            /** Status */
            status: string;
        };
        /** ErrorResponseSchema */
        ErrorResponseSchema: {
            /** Error */
            error: string;
            /** Error Code */
            error_code: string;
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
            /** Profile Picture */
            profile_picture: string | null;
            /** Is Active */
            is_active: boolean;
            /** Is Staff */
            is_staff: boolean;
            /** Created */
            created: string;
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
            organization_id?: string | null;
        };
        /** LoginRequest */
        LoginRequest: {
            /** Email */
            email: string;
            /** Password */
            password: string;
        };
        /** AgenticChatMessageResponse */
        AgenticChatMessageResponse: {
            /** Status */
            status: string;
        };
        /** AgenticChatMessageRequest */
        AgenticChatMessageRequest: {
            /** Message */
            message: string;
        };
        /** IntegrationAccountListItem */
        IntegrationAccountListItem: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Provider */
            provider: string;
            /** Display Name */
            display_name: string;
            /** Status */
            status: string;
            /** External Account Id */
            external_account_id: string;
            /**
             * Created
             * Format: date-time
             */
            created: string;
        };
        /** IntegrationAccountDetail */
        IntegrationAccountDetail: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Workspace Id */
            workspace_id: number;
            /** Provider */
            provider: string;
            /** Display Name */
            display_name: string;
            /** Status */
            status: string;
            /** External Account Id */
            external_account_id: string;
            /** Config */
            config: {
                [key: string]: unknown;
            };
            /** Last Synced At */
            last_synced_at: string | null;
            /** Last Error */
            last_error: string;
            /**
             * Created
             * Format: date-time
             */
            created: string;
            /**
             * Modified
             * Format: date-time
             */
            modified: string;
        };
        /** TaskExecutionListItem */
        TaskExecutionListItem: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Status */
            status: string;
            /** Requires Approval */
            requires_approval: boolean;
            /** Job Assignment Id */
            job_assignment_id: string | null;
            /** Job Role Name */
            job_role_name: string;
            /** Scheduled To */
            scheduled_to: string | null;
            /** Started At */
            started_at: string | null;
            /** Completed At */
            completed_at: string | null;
            /**
             * Created
             * Format: date-time
             */
            created: string;
        };
        /** ConversationListItem */
        ConversationListItem: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Status */
            status: string;
            /**
             * Cyber Identity Id
             * Format: uuid
             */
            cyber_identity_id: string;
            /** Cyber Identity Name */
            cyber_identity_name: string;
            /** External Thread Id */
            external_thread_id: string;
            /** External User Id */
            external_user_id: string;
            /** Message Count */
            message_count: number;
            /** Last Interaction At */
            last_interaction_at: string | null;
            /**
             * Created
             * Format: date-time
             */
            created: string;
        };
        /** WorkspaceResponse */
        WorkspaceResponse: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Organization Id */
            organization_id: string;
        };
        /** WorkspaceCreateRequest */
        WorkspaceCreateRequest: {
            /** Name */
            name: string;
        };
        /** CyberIdentityResponse */
        CyberIdentityResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Workspace Id */
            workspace_id: number;
            /** Type */
            type: string;
            /** Display Name */
            display_name: string;
            /** Is Active */
            is_active: boolean;
            /** Config */
            config: {
                [key: string]: unknown;
            };
            /**
             * Created
             * Format: date-time
             */
            created: string;
        };
        /** CyberIdentityCreateRequest */
        CyberIdentityCreateRequest: {
            /** Type */
            type: string;
            /** Display Name */
            display_name: string;
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /**
             * Config
             * @default {}
             */
            config: {
                [key: string]: unknown;
            };
        };
        /** CyberIdentityUpdateRequest */
        CyberIdentityUpdateRequest: {
            /** Type */
            type?: string | null;
            /** Display Name */
            display_name?: string | null;
            /** Is Active */
            is_active?: boolean | null;
            /** Config */
            config?: {
                [key: string]: unknown;
            } | null;
        };
        /** ActionableCatalogItem */
        ActionableCatalogItem: {
            /** Slug */
            slug: string;
            /** Name */
            name: string;
            /** Description */
            description: string;
            /** Provider */
            provider: string;
            /** Integration Account Id */
            integration_account_id: string;
            /** Integration */
            integration: {
                [key: string]: unknown;
            };
        };
        /** JobAssignmentResponse */
        JobAssignmentResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Workspace Id */
            workspace_id: number;
            /** Role Name */
            role_name: string;
            /** Description */
            description: string;
            /** Instructions */
            instructions: string;
            /** Enabled */
            enabled: boolean;
            /** Config */
            config: {
                [key: string]: unknown;
            };
            /**
             * Created
             * Format: date-time
             */
            created: string;
        };
        /** JobAssignmentCreateRequest */
        JobAssignmentCreateRequest: {
            /** Role Name */
            role_name: string;
            /**
             * Description
             * @default
             */
            description: string;
            /**
             * Instructions
             * @default
             */
            instructions: string;
            /**
             * Enabled
             * @default true
             */
            enabled: boolean;
            /**
             * Config
             * @default {}
             */
            config: {
                [key: string]: unknown;
            };
        };
        /** JobAssignmentUpdateRequest */
        JobAssignmentUpdateRequest: {
            /** Role Name */
            role_name?: string | null;
            /** Description */
            description?: string | null;
            /** Instructions */
            instructions?: string | null;
            /** Enabled */
            enabled?: boolean | null;
            /** Config */
            config?: {
                [key: string]: unknown;
            } | null;
        };
        /** TelegramConnectResponse */
        TelegramConnectResponse: {
            /**
             * Integration Account Id
             * Format: uuid
             */
            integration_account_id: string;
            /** Display Name */
            display_name: string;
        };
        /** TelegramConnectRequest */
        TelegramConnectRequest: {
            /** Bot Token */
            bot_token: string;
            /** Display Name */
            display_name?: string | null;
        };
        /** TelegramApproveResponse */
        TelegramApproveResponse: {
            /** Approved Telegram User Id */
            approved_telegram_user_id: string;
        };
        /** TelegramApproveRequest */
        TelegramApproveRequest: {
            /**
             * Integration Account Id
             * Format: uuid
             */
            integration_account_id: string;
            /** Code */
            code: string;
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
    core_routers_auth_list_my_organizations: {
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
    core_routers_agentic_chat_health: {
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
        };
    };
    core_routers_agentic_chat_send_message: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AgenticChatMessageRequest"];
            };
        };
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AgenticChatMessageResponse"];
                };
            };
        };
    };
    core_routers_workspaces_list_workspace_integrations: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
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
                    "application/json": components["schemas"]["IntegrationAccountListItem"][];
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
            /** @description Forbidden */
            403: {
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
    core_routers_workspaces_get_workspace_integration: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
                integration_account_id: string;
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
                    "application/json": components["schemas"]["IntegrationAccountDetail"];
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
            /** @description Forbidden */
            403: {
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
    core_routers_workspaces_list_integration_task_executions: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path: {
                workspace_id: number;
                integration_account_id: string;
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
                    "application/json": components["schemas"]["TaskExecutionListItem"][];
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
            /** @description Forbidden */
            403: {
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
    core_routers_workspaces_list_integration_conversations: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path: {
                workspace_id: number;
                integration_account_id: string;
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
                    "application/json": components["schemas"]["ConversationListItem"][];
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
            /** @description Forbidden */
            403: {
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
    core_routers_workspaces_list_workspaces: {
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
                    "application/json": components["schemas"]["WorkspaceResponse"][];
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
    core_routers_workspaces_create_workspace: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["WorkspaceCreateRequest"];
            };
        };
        responses: {
            /** @description Created */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WorkspaceResponse"];
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
    core_routers_workspaces_list_cyber_identities: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
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
                    "application/json": components["schemas"]["CyberIdentityResponse"][];
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
            /** @description Forbidden */
            403: {
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
    core_routers_workspaces_create_cyber_identity: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CyberIdentityCreateRequest"];
            };
        };
        responses: {
            /** @description Created */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CyberIdentityResponse"];
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
            /** @description Forbidden */
            403: {
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
    core_routers_workspaces_delete_cyber_identity: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
                cyber_identity_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description No Content */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
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
            /** @description Forbidden */
            403: {
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
    core_routers_workspaces_update_cyber_identity: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
                cyber_identity_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CyberIdentityUpdateRequest"];
            };
        };
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CyberIdentityResponse"];
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
            /** @description Forbidden */
            403: {
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
    core_routers_workspaces_list_workspace_actionables: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
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
                    "application/json": components["schemas"]["ActionableCatalogItem"][];
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
            /** @description Forbidden */
            403: {
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
    core_routers_workspaces_list_job_assignments: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
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
                    "application/json": components["schemas"]["JobAssignmentResponse"][];
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
            /** @description Forbidden */
            403: {
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
    core_routers_workspaces_create_job_assignment: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["JobAssignmentCreateRequest"];
            };
        };
        responses: {
            /** @description Created */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobAssignmentResponse"];
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
            /** @description Forbidden */
            403: {
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
    core_routers_workspaces_delete_job_assignment: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
                job_assignment_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description No Content */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
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
            /** @description Forbidden */
            403: {
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
    core_routers_workspaces_update_job_assignment: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
                job_assignment_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["JobAssignmentUpdateRequest"];
            };
        };
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobAssignmentResponse"];
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
            /** @description Forbidden */
            403: {
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
    core_routers_integrations_telegram_telegram_webhook: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                webhook_path_token: string;
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
                content?: never;
            };
        };
    };
    core_routers_integrations_telegram_telegram_connect: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TelegramConnectRequest"];
            };
        };
        responses: {
            /** @description Created */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TelegramConnectResponse"];
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
            /** @description Forbidden */
            403: {
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
    core_routers_integrations_telegram_telegram_approve_sender: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TelegramApproveRequest"];
            };
        };
        responses: {
            /** @description OK */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TelegramApproveResponse"];
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
            /** @description Forbidden */
            403: {
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
    core_routers_integrations_telegram_telegram_disconnect: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                workspace_id: number;
                integration_account_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description No Content */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
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
            /** @description Forbidden */
            403: {
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
}
