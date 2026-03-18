import openapiTS, { astToString } from 'openapi-typescript'
import path from 'path'
import fs from 'fs'
import ts from 'typescript'
import { fileURLToPath } from 'url'

const OPENAPI_SPEC_PATH = process.argv[2] || 'http://localhost:8000/api/openapi.json'

const BLOB = ts.factory.createIdentifier('Blob') // `Blob`
const NULL = ts.factory.createLiteralTypeNode(ts.factory.createNull()) // `null`

const baseDir = path.dirname(fileURLToPath(import.meta.url))
const projectRoot = path.resolve(baseDir, '..')

console.log(`🌐 Fetching OpenAPI schema from: ${OPENAPI_SPEC_PATH}`)

try {
  const ast = await openapiTS(OPENAPI_SPEC_PATH, {
    transform(schemaObject, metadata) {
      // Handle binary format (for file uploads)
      if (schemaObject.format === 'binary') {
        return {
          schema: schemaObject.nullable ? ts.factory.createUnionTypeNode([BLOB, NULL]) : BLOB,
        }
      }
      
      // Handle date-time formats
      if (schemaObject.format === 'date-time' || schemaObject.format === 'date') {
        return {
          schema: ts.factory.createTypeReferenceNode('string'),
        }
      }
      
      // Handle file uploads and images specifically (with word boundaries to avoid matching "Profile")
      if (schemaObject.format === 'binary' || 
          (metadata.path && (
            /\/(upload|image|avatar|photo|document|attachment)\b/i.test(metadata.path) ||
            /_file$|_image$|_photo$|_avatar$|_document$/i.test(metadata.path)
          ))) {
        return {
          schema: ts.factory.createUnionTypeNode([
            BLOB,
            ts.factory.createTypeReferenceNode('string'), // URL
            NULL
          ]),
        }
      }
    },
  })
  
  const contents = astToString(ast)
  
  // Create the API types directory
  const apiTypesDir = path.resolve(projectRoot, './types/api')
  await fs.promises.mkdir(apiTypesDir, { recursive: true })
  
  // Write the generated schema
  const outputPath = path.resolve(apiTypesDir, 'schema.d.ts')
  await fs.promises.writeFile(outputPath, contents)
  
  console.log(`✅ Generated TypeScript schema at: ${outputPath}`)
  
} catch (error) {
  console.error('❌ Error generating schema:', error.message)
  process.exit(1)
}