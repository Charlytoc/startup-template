# API Type Generation

This directory contains scripts for automatically generating TypeScript types from your Django backend's OpenAPI schema.

## How it works

The `generate-schema.mjs` script:
1. Fetches the OpenAPI JSON schema from your Django backend
2. Uses `openapi-typescript` to generate comprehensive TypeScript types
3. Creates both the raw schema types and convenient type aliases
4. Handles special cases like binary files, date formats, etc.

## Usage

### Generate types from local development server
```bash
npm run generate-api-types:dev
```

### Generate types from production server
```bash
npm run generate-api-types:prod
```

### Generate types from custom URL
```bash
npm run generate-api-types http://your-api-url.com/api/openapi.json
```

## Generated Files

- `types/api/schema.d.ts` - Raw OpenAPI schema types (auto-generated)
- `types/api/types.ts` - Convenient type aliases and helper types

## Integration

The generated types are automatically imported in:
- `services/api.ts` - Legacy API service (partially typed)
- `services/typed-api.ts` - New fully type-safe API client

## Type Safety Benefits

1. **Compile-time validation** - Catch API mismatches before runtime
2. **Auto-completion** - IDE support for all API endpoints and data structures
3. **Refactoring safety** - Changes to backend automatically update frontend types
4. **Documentation** - Types serve as living documentation

## Workflow

1. Make changes to your Django API (add/modify endpoints, schemas)
2. Run `npm run generate-api-types:dev` to update types
3. Update your frontend code to use new types
4. Enjoy compile-time type safety!

## Troubleshooting

### Schema generation fails
- Ensure your Django server is running
- Check that the OpenAPI endpoint is accessible
- Verify the URL is correct

### Types are outdated
- Re-run the generation script after backend changes
- Consider adding this to your CI/CD pipeline

### Type errors after generation
- Check that your API endpoints match the generated schema
- Verify request/response data structures
- Update your code to match the new types
