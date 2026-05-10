import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Multimedia, Post
import boto3
import uuid
import os

@login_required
def get_upload_url(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({'error': 'invalid json'}, status=400)

    filename = data.get('name')
    file_type = data.get('type')

    if not filename or not file_type:
        return JsonResponse({'error': 'missing fields'}, status=400)

    ext = os.path.splitext(filename)[1].lower()
    unique_key = f"uploads/{uuid.uuid4().hex}{ext}"

    s3 = boto3.client('s3', region_name='us-east-1')
    presigned = s3.generate_presigned_post(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=unique_key,
        Fields={'Content-Type': file_type},
        Conditions=[
            {'Content-Type': file_type},
            ['content-length-range', 1, 524288000],
        ],
        ExpiresIn=3600
    )

    return JsonResponse({
        'url': presigned['url'],
        'fields': presigned['fields'],
        'key': unique_key,
    })


@csrf_exempt
def compression_callback(request):
    """Lambda calls this when compression is done."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid json'}, status=400)

    # Verify secret
    if data.get('secret') != settings.LAMBDA_CALLBACK_SECRET:
        return JsonResponse({'error': 'unauthorized'}, status=401)

    filename = data.get('filename')
    status = data.get('status')
    original_key = data.get('original_key')

    if status == 'ok':
        # Build the final compressed URL
        compressed_key = 'compressed/' + original_key.split('uploads/', 1)[-1]
        # Handle format change (heic → jpg etc)
        compressed_key = os.path.splitext(compressed_key)[0] + os.path.splitext(filename)[1]
        
        compressed_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{compressed_key}"

        # Determine tipo_multimedia
        ext = os.path.splitext(filename)[1].lower()
        video_exts = {'.mp4', '.mov', '.avi', '.webm', '.mkv', '.flv', '.wmv'}
        tipo = 'video' if ext in video_exts else 'imagen'

        # Find the pending Multimedia record and update it
        # (we'll create it as 'pending' from the upload view below)
        try:
            multimedia = Multimedia.objects.get(
                url__contains=os.path.splitext(os.path.basename(original_key))[0],
                tipo_multimedia='pending'
            )
            multimedia.url = compressed_url
            multimedia.tipo_multimedia = tipo
            multimedia.save()
        except Multimedia.DoesNotExist:
            # If not found, create it (fallback)
            # You'd need post_id somehow — better to pass it from upload view
            pass

    elif status == 'error':
        # Optionally mark it as failed in your DB
        pass

    return JsonResponse({'ok': True})


#
@login_required
def create_multimedia(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid json'}, status=400)

    s3_url = data.get('url')
    post_id = data.get('post_id')
    contenido_id = data.get('contenido_id')  # new

    if not s3_url or (not post_id and not contenido_id):
        return JsonResponse({'error': 'missing fields'}, status=400)

    if contenido_id:
        from .models import ContenidoEducativo
        try:
            contenido = ContenidoEducativo.objects.get(
                id=contenido_id,
                colegio=request.user.centro_educacional
            )
        except ContenidoEducativo.DoesNotExist:
            return JsonResponse({'error': 'contenido not found'}, status=404)

        multimedia = Multimedia.objects.create(
            contenido_educativo=contenido,
            url=s3_url,
            tipo_multimedia='pending',
            status='pending',
        )
    else:
        try:
            post = Post.objects.get(id=post_id, autor=request.user)
        except Post.DoesNotExist:
            return JsonResponse({'error': 'post not found'}, status=404)

        multimedia = Multimedia.objects.create(
            post=post,
            url=s3_url,
            tipo_multimedia='pending',
            status='pending',
        )

    return JsonResponse({
        'ok': True,
        'id': multimedia.id,
        'message': 'Upload received, compression in progress'
    })