import openapiTS, { astToString } from "openapi-typescript";
import path from "path";
import fs from "fs";
import ts from "typescript";
import { fileURLToPath } from "url";

const OPENAPI_SPEC_PATH = process.argv[2] ?? "http://localhost:8000/api/openapi.json";

const BLOB = ts.factory.createIdentifier("Blob");
const NULL = ts.factory.createLiteralTypeNode(ts.factory.createNull());

const baseDir = path.dirname(fileURLToPath(import.meta.url));
const outputDir = path.resolve(baseDir, "../src/lib/api");
const outputFile = path.resolve(outputDir, "schema.d.ts");

try {
  const ast = await openapiTS(OPENAPI_SPEC_PATH, {
    transform(schemaObject) {
      if (schemaObject.format === "binary") {
        return {
          schema: schemaObject.nullable ? ts.factory.createUnionTypeNode([BLOB, NULL]) : BLOB,
        };
      }
      return undefined;
    },
  });

  const contents = astToString(ast);
  await fs.promises.mkdir(outputDir, { recursive: true });
  await fs.promises.writeFile(outputFile, contents);

  console.log(`Generated OpenAPI types from: ${OPENAPI_SPEC_PATH}`);
  console.log(`Output: ${outputFile}`);
} catch (error) {
  console.error("Failed to generate OpenAPI types.");
  console.error(`Source: ${OPENAPI_SPEC_PATH}`);
  console.error(error);
  process.exit(1);
}
