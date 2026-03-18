# Storage Configuration

Este documento explica cómo configurar el almacenamiento de archivos (imágenes) en la aplicación Speaky.ai.

## Configuración Local (Desarrollo)

Por defecto, la aplicación está configurada para usar almacenamiento local durante el desarrollo.

### Archivos Media
- **Ubicación**: `django/media/`
- **URL**: `http://localhost:8000/media/`
- **Estructura**:
  - `tutors/avatars/` - Avatares de tutores AI
  - `users/profile_pictures/` - Fotos de perfil de usuarios

### Configuración
No se requiere configuración adicional para desarrollo local. Los archivos se sirven automáticamente cuando `DEBUG=True`.

## Configuración S3 (Producción)

Para usar AWS S3 en producción, configura las siguientes variables de entorno:

### Variables de Entorno Requeridas

```bash
# Habilitar S3
USE_S3=True

# Credenciales AWS
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_REGION_NAME=us-east-1  # Opcional, por defecto us-east-1
```

### Configuración del Bucket S3

1. **Crear bucket S3**:
   - Nombre: `speaky-ai-media` (o el que prefieras)
   - Región: `us-east-1` (o la que prefieras)
   - Configuración pública: Habilitar para lectura pública

2. **Política de bucket** (opcional, para acceso público):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

3. **CORS Configuration** (si necesitas acceso desde frontend):
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

### Migración de Local a S3

1. **Instalar dependencias**:
```bash
pip install django-storages==1.14.6 boto3 Pillow
```

2. **Configurar variables de entorno** en tu servidor de producción

3. **Ejecutar migraciones**:
```bash
python manage.py migrate
```

4. **Migrar archivos existentes** (si los hay):
```bash
python manage.py collectstatic --noinput
```

## Uso en el Código

### Modelos
Los campos de imagen están disponibles en:

- **AiTutor**: `avatar_url` - Imagen del avatar del tutor
- **User**: `profile_picture` - Foto de perfil del usuario

### Ejemplo de uso en Django Admin
```python
# En admin.py
class AiTutorAdmin(admin.ModelAdmin):
    list_display = ['name', 'avatar_url']
    readonly_fields = ['created', 'modified']
```

### Ejemplo de uso en API
```python
# En serializers
class AiTutorSerializer(serializers.ModelSerializer):
    avatar_url = serializers.ImageField(read_only=True)
    
    class Meta:
        model = AiTutor
        fields = ['id', 'name', 'personality', 'avatar_url']
```

## Costos Estimados (AWS S3)

- **Almacenamiento**: ~$0.023 por GB/mes
- **Requests**: ~$0.0004 por 1,000 requests GET
- **Transfer out**: Primeros 1GB gratis, luego ~$0.09 por GB

Para una aplicación pequeña-mediana:
- 1GB de imágenes: ~$0.023/mes
- 10,000 requests/mes: ~$0.004/mes
- **Total estimado**: <$0.05/mes

## Troubleshooting

### Error: "No module named 'storages'"
```bash
pip install django-storages==1.14.6
```

### Error: "Access Denied" en S3
- Verificar credenciales AWS
- Verificar permisos del bucket
- Verificar región configurada

### Imágenes no se cargan en desarrollo
- Verificar que `DEBUG=True`
- Verificar configuración en `urls.py`
- Verificar que la carpeta `media/` existe

### Imágenes no se cargan en producción
- Verificar variables de entorno
- Verificar configuración CORS del bucket
- Verificar que `USE_S3=True`
