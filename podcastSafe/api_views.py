from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Q, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from datetime import timedelta, datetime
import logging
import os
import shutil

import subprocess
import signal
import sys

# Chemins supplémentaires où chercher FFmpeg (WinGet sur Windows)
_FFMPEG_FALLBACK_PATHS = [
    r'C:\Users\couli\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe',
    r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
]

def _find_ffmpeg():
    """Retourne le chemin de ffmpeg ou None."""
    found = shutil.which('ffmpeg')
    if found:
        return found
    for p in _FFMPEG_FALLBACK_PATHS:
        if os.path.isfile(p):
            return p
    return None

from .models import Episode, Category, LiveStream, Subscription, ContactMessage, Comment, MultiStreamConfig, Event

# Registre des processus FFmpeg actifs (en mémoire — single worker)
_FFMPEG_PROCS = {}  # config_id -> subprocess.Popen

# ── Helpers RTMP ──────────────────────────────────────────────────────────────
import re as _re
_RTMP_RE = _re.compile(r'^rtmps?://[^\s\r\n\x00;&|`$<>\'\"\\]{10,}$')

def _validate_rtmp_url(url: str) -> bool:
    """Vérifie qu'une URL RTMP est bien formée et sans injection shell."""
    return bool(_RTMP_RE.match(url.strip())) if url and url.strip() else True  # vide = OK

def _mask_rtmp(url: str) -> str:
    """Retourne une version masquée pour affichage (jamais la vraie clé)."""
    if not url:
        return ''
    url = url.strip()
    # Garder le début (domaine) + masquer la clé
    parts = url.split('/')
    if len(parts) >= 4:
        visible = '/'.join(parts[:3]) + '/'
        return visible + '••••••••'
    return url[:20] + '••••••••'

logger = logging.getLogger(__name__)

class IsDashboardOrAdmin(BasePermission):
    """Accès API : clé API valide (≥16 chars) OU utilisateur staff/superuser."""
    def has_permission(self, request, view):
        api_key = (request.META.get('HTTP_X_API_KEY') or '').strip()
        expected_key = getattr(settings, 'DASHBOARD_API_KEY', None) or ''
        # Clé API : longueur minimale 16 + correspondance exacte
        if len(api_key) >= 16 and len(expected_key) >= 16 and api_key == expected_key:
            return True
        # Session Django : staff ou superuser uniquement
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )



# ──────────────────────────────────────────────
# Dashboard Data
# ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsDashboardOrAdmin])
def dashboard_data(request):
    """API endpoint pour fournir les données du dashboard"""
    try:
        total_episodes = Episode.objects.count()
        total_messages = ContactMessage.objects.count()
        unread_messages = ContactMessage.objects.filter(is_read=False).count()
        active_lives = LiveStream.objects.filter(status='live').count()
        total_subscribers = Subscription.objects.filter(is_active=True).count()

        # Épisodes récents
        recent_episodes = Episode.objects.order_by('-created_at')[:5]
        recent_episodes_data = [
            {
                'id': ep.id,
                'title': ep.title,
                'description': (ep.description or '')[:100],
                'created_at': ep.created_at.strftime('%Y-%m-%d'),
                'status': 'published' if ep.is_published else 'draft',
                'views': ep.views_count,
                'episode_type': ep.episode_type,
            }
            for ep in recent_episodes
        ]

        # Messages récentes
        recent_messages = ContactMessage.objects.order_by('-created_at')[:5]
        recent_messages_data = [
            {
                'id': m.id,
                'name': m.name,
                'email': m.email,
                'subject': m.subject,
                'created_at': m.created_at.strftime('%Y-%m-%d'),
                'read': m.is_read,
            }
            for m in recent_messages
        ]

        # Stats 30 derniers jours
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_stats = {
            'new_episodes': Episode.objects.filter(created_at__gte=thirty_days_ago).count(),
            'active_streams': LiveStream.objects.filter(status='live').count(),
        }

        data = {
            'stats': {
                'total_episodes': total_episodes,
                'total_messages': total_messages,
                'unread_messages': unread_messages,
                'active_lives': active_lives,
                'total_subscribers': total_subscribers,
            },
            'recent_data': {
                'recent_episodes': recent_episodes_data,
                'recent_messages': recent_messages_data,
            },
            'recent_stats': recent_stats,
            'last_updated': timezone.now().isoformat(),
        }

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in dashboard_data API: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ──────────────────────────────────────────────
# Episodes
# ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsDashboardOrAdmin])
def episodes_api(request):
    """Liste des épisodes avec pagination et filtrage"""
    try:
        page = max(1, int(request.GET.get('page', 1)))
        page_size = max(1, min(int(request.GET.get('page_size', 20)), 100))
        status_filter = request.GET.get('status', '')
        search = request.GET.get('search', '')
        episode_type = request.GET.get('type', '')

        queryset = Episode.objects.all()

        if status_filter == 'published':
            queryset = queryset.filter(is_published=True)
        elif status_filter == 'draft':
            queryset = queryset.filter(is_published=False)

        if episode_type:
            queryset = queryset.filter(episode_type=episode_type)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        total = queryset.count()
        start = (page - 1) * page_size
        episodes = queryset.order_by('-created_at')[start:start + page_size]

        episodes_data = [
            {
                'id': ep.id,
                'title': ep.title,
                'description': (ep.description or '')[:200],
                'episode_type': ep.episode_type,
                'category': ep.category.name if ep.category else None,
                'category_id': ep.category_id,
                'is_published': ep.is_published,
                'audio_url': ep.audio_url,
                'video_url': ep.video_url,
                'duration': ep.duration,
                'cover_color': ep.cover_color,
                'views': ep.views_count,
                'created_at': ep.created_at.strftime('%Y-%m-%d'),
            }
            for ep in episodes
        ]

        return Response({
            'episodes': episodes_data,
            'pagination': {
                'page': page, 'page_size': page_size,
                'total': total, 'pages': (total + page_size - 1) // page_size
            }
        })

    except Exception as e:
        logger.error(f"Error in episodes_api: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsDashboardOrAdmin])
def episode_create(request):
    """Créer un épisode depuis le dashboard"""
    try:
        data = request.data
        title = (data.get('title') or '').strip()
        description = (data.get('description') or '').strip()
        episode_type = data.get('episode_type', 'podcast')
        category_id = data.get('category_id')
        audio_url = (data.get('audio_url') or '').strip()
        video_url = (data.get('video_url') or '').strip()
        duration = (data.get('duration') or '').strip()
        cover_color = data.get('cover_color', '#00261b')

        if not title or not description:
            return Response({'error': 'Titre et description obligatoires'}, status=400)

        category = None
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                pass

        episode = Episode.objects.create(
            title=title,
            description=description,
            episode_type=episode_type,
            category=category,
            audio_url=audio_url,
            video_url=video_url,
            duration=duration,
            cover_color=cover_color,
            is_published=True,
        )

        return Response({
            'success': True,
            'episode': {
                'id': episode.id,
                'title': episode.title,
                'created_at': episode.created_at.strftime('%Y-%m-%d'),
            }
        }, status=201)

    except Exception as e:
        logger.error(f"Error in episode_create: {str(e)}")
        return Response({'error': str(e)}, status=500)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsDashboardOrAdmin])
def episode_update(request, pk):
    """Mettre à jour un épisode depuis le dashboard"""
    try:
        episode = Episode.objects.get(id=pk)
        data = request.data
        str_fields = ['title', 'description', 'episode_type', 'audio_url', 'video_url', 'duration', 'host', 'cover_color']
        for field in str_fields:
            if field in data and data[field] is not None:
                setattr(episode, field, str(data[field]).strip())
        if 'is_published' in data:
            val = data['is_published']
            episode.is_published = val if isinstance(val, bool) else str(val).lower() in ('true', '1', 'yes')
        if 'category_id' in data:
            cid = data['category_id']
            if cid:
                try:
                    episode.category = Category.objects.get(id=int(cid))
                except (Category.DoesNotExist, ValueError):
                    pass
            else:
                episode.category = None
        episode.save()
        return Response({'success': True, 'id': episode.id})
    except Episode.DoesNotExist:
        return Response({'error': 'Épisode non trouvé'}, status=404)
    except Exception as e:
        logger.error(f"Error in episode_update: {str(e)}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsDashboardOrAdmin])
@parser_classes([MultiPartParser, FormParser])
def episode_upload_file(request, pk):
    """Upload un fichier vidéo/audio pour un épisode existant"""
    try:
        episode = Episode.objects.get(id=pk)
        if 'video_file' in request.FILES:
            episode.video_file = request.FILES['video_file']
            episode.save()
            url = request.build_absolute_uri(episode.video_file.url)
            return Response({'success': True, 'url': url})
        return Response({'error': 'Aucun fichier fourni (champ: video_file)'}, status=400)
    except Episode.DoesNotExist:
        return Response({'error': 'Épisode non trouvé'}, status=404)
    except Exception as e:
        logger.error(f"Error in episode_upload_file: {str(e)}")
        return Response({'error': str(e)}, status=500)


@api_view(['DELETE'])
@permission_classes([IsDashboardOrAdmin])
def episode_delete(request, pk):
    """Supprimer un épisode"""
    try:
        episode = Episode.objects.get(id=pk)
        episode.delete()
        return Response({'success': True})
    except Episode.DoesNotExist:
        return Response({'error': 'Épisode non trouvé'}, status=404)
    except Exception as e:
        logger.error(f"Error in episode_delete: {str(e)}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsDashboardOrAdmin])
def categories_api(request):
    cats = Category.objects.all()
    return Response({
        'categories': [{'id': c.id, 'name': c.name, 'icon': c.icon, 'color': c.color, 'for_type': c.for_type} for c in cats]
    })


@api_view(['POST'])
@permission_classes([IsDashboardOrAdmin])
def category_create(request):
    name = request.data.get('name', '').strip()
    if not name:
        return Response({'error': 'Nom requis'}, status=400)
    cat = Category.objects.create(
        name=name,
        icon=request.data.get('icon', 'church'),
        color=request.data.get('color', '#00261b'),
        for_type=request.data.get('for_type', 'all'),
    )
    return Response({'category': {'id': cat.id, 'name': cat.name, 'icon': cat.icon, 'color': cat.color, 'for_type': cat.for_type}}, status=201)


@api_view(['PUT'])
@permission_classes([IsDashboardOrAdmin])
def category_update(request, pk):
    try:
        cat = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return Response({'error': 'Introuvable'}, status=404)
    for field in ('name', 'icon', 'color', 'for_type'):
        if field in request.data:
            setattr(cat, field, request.data[field])
    cat.save()
    return Response({'category': {'id': cat.id, 'name': cat.name, 'icon': cat.icon, 'color': cat.color, 'for_type': cat.for_type}})


@api_view(['DELETE'])
@permission_classes([IsDashboardOrAdmin])
def category_delete(request, pk):
    try:
        Category.objects.get(pk=pk).delete()
    except Category.DoesNotExist:
        return Response({'error': 'Introuvable'}, status=404)
    return Response({'ok': True})


# ──────────────────────────────────────────────
# Live Streams
# ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsDashboardOrAdmin])
def livestreams_api(request):
    """Liste des live streams"""
    try:
        streams = LiveStream.objects.all().order_by('-created_at')
        data = [
            {
                'id': s.id,
                'title': s.title,
                'description': s.description,
                'platform': s.platform,
                'platform_display': s.get_platform_display(),
                'stream_url': s.stream_url,
                'embed_url': s.embed_url,
                'status': s.status,
                'status_display': s.get_status_display(),
                'viewers_count': s.viewers_count,
                'scheduled_at': s.scheduled_at.strftime('%Y-%m-%d %H:%M') if s.scheduled_at else None,
                'created_at': s.created_at.strftime('%Y-%m-%d'),
            }
            for s in streams
        ]
        return Response({
            'livestreams': data,
            'platforms': [{'value': k, 'label': v} for k, v in LiveStream.PLATFORM_CHOICES],
            'statuses': [{'value': k, 'label': v} for k, v in LiveStream.STATUS_CHOICES],
        })
    except Exception as e:
        logger.error(f"Error in livestreams_api: {str(e)}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsDashboardOrAdmin])
def livestream_create(request):
    """Créer un live stream"""
    try:
        data = request.data
        title = (data.get('title') or '').strip()
        if not title:
            return Response({'error': 'Titre obligatoire'}, status=400)

        stream = LiveStream.objects.create(
            title=title,
            description=(data.get('description') or '').strip(),
            platform=data.get('platform', 'youtube'),
            stream_url=(data.get('stream_url') or '').strip(),
            embed_url=(data.get('embed_url') or '').strip(),
            status=data.get('status', 'scheduled'),
        )
        return Response({'success': True, 'id': stream.id}, status=201)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['PUT'])
@permission_classes([IsDashboardOrAdmin])
def livestream_update(request, pk):
    """Mettre à jour un live stream"""
    try:
        stream = LiveStream.objects.get(id=pk)
        data = request.data
        for field in ['title', 'description', 'platform', 'stream_url', 'embed_url', 'status']:
            val = data.get(field)
            if val is not None:
                setattr(stream, field, val.strip() if isinstance(val, str) else val)
        stream.save()
        return Response({'success': True})
    except LiveStream.DoesNotExist:
        return Response({'error': 'Live non trouvé'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['DELETE'])
@permission_classes([IsDashboardOrAdmin])
def livestream_delete(request, pk):
    """Supprimer un live stream"""
    try:
        LiveStream.objects.get(id=pk).delete()
        return Response({'success': True})
    except LiveStream.DoesNotExist:
        return Response({'error': 'Live non trouvé'}, status=404)


# ──────────────────────────────────────────────
# Messages (Contact)
# ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsDashboardOrAdmin])
def messages_api(request):
    """Liste des messages de contact"""
    try:
        status_filter = request.GET.get('status', '')
        priority = request.GET.get('priority', '')
        search = request.GET.get('search', '')

        queryset = ContactMessage.objects.all()
        if status_filter == 'read':
            queryset = queryset.filter(is_read=True)
        elif status_filter == 'unread':
            queryset = queryset.filter(is_read=False)
        if priority:
            queryset = queryset.filter(priority=priority)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(subject__icontains=search) | Q(email__icontains=search)
            )

        messages_list = queryset.order_by('-created_at')
        data = [
            {
                'id': m.id,
                'name': m.name,
                'email': m.email,
                'subject': m.subject,
                'message': m.message,
                'priority': m.priority,
                'read': m.is_read,
                'created_at': m.created_at.strftime('%Y-%m-%d'),
            }
            for m in messages_list
        ]

        stats = {
            'total': ContactMessage.objects.count(),
            'unread': ContactMessage.objects.filter(is_read=False).count(),
            'high_priority': ContactMessage.objects.filter(priority='high').count(),
            'read': ContactMessage.objects.filter(is_read=True).count(),
        }

        return Response({'messages': data, 'stats': stats})
    except Exception as e:
        logger.error(f"Error in messages_api: {str(e)}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsDashboardOrAdmin])
def message_mark_read(request, pk):
    """Marquer un message comme lu"""
    try:
        msg = ContactMessage.objects.get(id=pk)
        msg.is_read = True
        msg.save()
        return Response({'success': True})
    except ContactMessage.DoesNotExist:
        return Response({'error': 'Message non trouvé'}, status=404)


@api_view(['DELETE'])
@permission_classes([IsDashboardOrAdmin])
def message_delete(request, pk):
    """Supprimer un message"""
    try:
        ContactMessage.objects.get(id=pk).delete()
        return Response({'success': True})
    except ContactMessage.DoesNotExist:
        return Response({'error': 'Message non trouvé'}, status=404)


@api_view(['POST'])
@permission_classes([IsDashboardOrAdmin])
def message_mark_all_read(request):
    """Marquer tous les messages comme lus"""
    ContactMessage.objects.filter(is_read=False).update(is_read=True)
    return Response({'success': True})


# ──────────────────────────────────────────────
# Subscriptions
# ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsDashboardOrAdmin])
def subscriptions_api(request):
    """Liste des abonnements"""
    try:
        subs = Subscription.objects.all().order_by('-created_at')
        data = [
            {
                'id': s.id,
                'first_name': s.first_name,
                'last_name': s.last_name,
                'email': s.email,
                'notify_podcasts': s.notify_podcasts,
                'notify_live': s.notify_live,
                'notify_videos': s.notify_videos,
                'is_active': s.is_active,
                'created_at': s.created_at.strftime('%Y-%m-%d'),
            }
            for s in subs
        ]
        stats = {
            'total': Subscription.objects.count(),
            'active': Subscription.objects.filter(is_active=True).count(),
        }
        return Response({'subscriptions': data, 'stats': stats})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['DELETE'])
@permission_classes([IsDashboardOrAdmin])
def subscription_delete(request, pk):
    """Supprimer un abonné"""
    try:
        sub = get_object_or_404(Subscription, pk=pk)
        sub.delete()
        return Response({'success': True})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsDashboardOrAdmin])
@parser_classes([MultiPartParser, FormParser])
def episode_upload_chunk(request, pk):
    """Upload par chunks pour les très gros fichiers vidéo"""
    import tempfile
    try:
        episode = get_object_or_404(Episode, pk=pk)
        chunk = request.FILES.get('chunk')
        chunk_index = int(request.data.get('chunk_index', 0))
        total_chunks = int(request.data.get('total_chunks', 1))
        filename = request.data.get('filename', f'video_{pk}.mp4')
        upload_id = request.data.get('upload_id', str(pk))

        if not chunk:
            return Response({'error': 'Aucun chunk fourni'}, status=400)

        # Utilise /tmp — toujours disponible et inscriptible sur Render/Linux
        tmp_dir = os.path.join(tempfile.gettempdir(), '_sp_chunks', upload_id)
        os.makedirs(tmp_dir, exist_ok=True)
        chunk_path = os.path.join(tmp_dir, f'{chunk_index:06d}')
        with open(chunk_path, 'wb') as f:
            for data in chunk.chunks():
                f.write(data)

        if chunk_index == total_chunks - 1:
            year_month = datetime.now().strftime('%Y/%m')
            safe_name = ''.join(c if c.isalnum() or c in '._-' else '_' for c in filename)
            dest_path = os.path.join(tempfile.gettempdir(), safe_name)
            with open(dest_path, 'wb') as outfile:
                for i in range(total_chunks):
                    cp = os.path.join(tmp_dir, f'{i:06d}')
                    with open(cp, 'rb') as infile:
                        shutil.copyfileobj(infile, outfile)
            shutil.rmtree(tmp_dir, ignore_errors=True)

            from django.core.files import File
            upload_path = f'videos/{year_month}/{safe_name}'
            with open(dest_path, 'rb') as f:
                episode.video_file.save(upload_path, File(f), save=True)
            try:
                os.remove(dest_path)
            except OSError:
                pass

            url = episode.video_file.url
            return Response({'success': True, 'done': True, 'url': url})

        return Response({'success': True, 'done': False, 'received': chunk_index + 1, 'total': total_chunks})
    except Exception as e:
        logger.error(f"Error in episode_upload_chunk: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)


# ──────────────────────────────────────────────
# Analytics
# ──────────────────────────────────────────────

# ──────────────────────────────────────────────
# Comments
# ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsDashboardOrAdmin])
def comments_api(request):
    """Liste des commentaires avec filtrage."""
    try:
        approved_filter = request.GET.get('approved', '')
        episode_id = request.GET.get('episode_id', '')
        search = request.GET.get('search', '')

        queryset = Comment.objects.select_related('episode').all()
        if approved_filter == 'true':
            queryset = queryset.filter(is_approved=True)
        elif approved_filter == 'false':
            queryset = queryset.filter(is_approved=False)
        if episode_id:
            queryset = queryset.filter(episode_id=episode_id)
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(author_name__icontains=search) | Q(content__icontains=search)
            )

        data = [
            {
                'id': c.id,
                'episode_id': c.episode_id,
                'episode_title': c.episode.title,
                'author_name': c.author_name,
                'author_email': c.author_email,
                'content': c.content,
                'is_approved': c.is_approved,
                'created_at': c.created_at.strftime('%Y-%m-%d %H:%M'),
            }
            for c in queryset.order_by('-created_at')
        ]

        stats = {
            'total': Comment.objects.count(),
            'approved': Comment.objects.filter(is_approved=True).count(),
            'pending': Comment.objects.filter(is_approved=False).count(),
        }

        return Response({'comments': data, 'stats': stats})
    except Exception as e:
        logger.error(f"Error in comments_api: {str(e)}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsDashboardOrAdmin])
def comment_approve(request, pk):
    """Approuver ou désapprouver un commentaire."""
    try:
        comment = Comment.objects.get(id=pk)
        comment.is_approved = not comment.is_approved
        comment.save()
        return Response({'success': True, 'is_approved': comment.is_approved})
    except Comment.DoesNotExist:
        return Response({'error': 'Commentaire non trouvé'}, status=404)


@api_view(['DELETE'])
@permission_classes([IsDashboardOrAdmin])
def comment_delete(request, pk):
    """Supprimer un commentaire."""
    try:
        Comment.objects.get(id=pk).delete()
        return Response({'success': True})
    except Comment.DoesNotExist:
        return Response({'error': 'Commentaire non trouvé'}, status=404)


@api_view(['GET'])
@permission_classes([IsDashboardOrAdmin])
def analytics_data(request):
    """Analytics détaillées"""
    try:
        days = int(request.GET.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)

        # Top épisodes
        top_episodes = Episode.objects.order_by('-views_count')[:10]

        # Totaux
        total_views = Episode.objects.aggregate(total=Sum('views_count'))['total'] or 0
        total_messages = ContactMessage.objects.count()
        total_subs = Subscription.objects.filter(is_active=True).count()

        # Par catégorie
        categories = Category.objects.annotate(
            episode_count=Count('episode')
        ).order_by('-episode_count')[:5]

        data = {
            'total_views': total_views,
            'total_messages': total_messages,
            'total_subscribers': total_subs,
            'total_episodes': Episode.objects.count(),
            'top_episodes': [
                {'id': ep.id, 'title': ep.title, 'views': ep.views_count, 'type': ep.episode_type}
                for ep in top_episodes
            ],
            'categories': [
                {'name': c.name, 'count': c.episode_count}
                for c in categories
            ],
            'period_days': days,
        }

        return Response(data)
    except Exception as e:
        logger.error(f"Error in analytics_data: {str(e)}")
        return Response({'error': str(e)}, status=500)


# ──────────────────────────────────────────────
# Multistream
# ──────────────────────────────────────────────

def _get_or_create_config():
    cfg, _ = MultiStreamConfig.objects.get_or_create(pk=1, defaults={'title': 'Studio SafePlace'})
    return cfg


@api_view(['GET', 'POST'])
@permission_classes([IsDashboardOrAdmin])
def multistream_config(request):
    """Lire ou mettre à jour la configuration RTMP.
    Les clés RTMP ne sont JAMAIS retournées en clair — seulement masquées.
    En POST, un champ vide = on garde la clé existante.
    """
    cfg = _get_or_create_config()
    if request.method == 'POST':
        data = request.data
        cfg.title         = (data.get('title') or cfg.title)[:200]
        valid_qualities   = [c[0] for c in cfg.VIDEO_QUALITY_CHOICES]
        if data.get('video_quality') in valid_qualities:
            cfg.video_quality = data['video_quality']

        # Clés RTMP : ne mettre à jour que si une nouvelle valeur non-vide est fournie
        for field in ('youtube_rtmp', 'tiktok_rtmp', 'instagram_rtmp', 'custom_rtmp'):
            new_val = (data.get(field) or '').strip()
            if new_val:
                if not _validate_rtmp_url(new_val):
                    return Response(
                        {'error': f'URL RTMP invalide pour {field} (doit commencer par rtmp:// ou rtmps://)'},
                        status=400,
                    )
                setattr(cfg, field, new_val)
        cfg.save()

    return Response({
        'id': cfg.pk,
        'title': cfg.title,
        'status': cfg.status,
        # Clés masquées — jamais les vraies valeurs
        'youtube_rtmp':   _mask_rtmp(cfg.youtube_rtmp),
        'tiktok_rtmp':    _mask_rtmp(cfg.tiktok_rtmp),
        'instagram_rtmp': _mask_rtmp(cfg.instagram_rtmp),
        'custom_rtmp':    _mask_rtmp(cfg.custom_rtmp),
        # Booléens pour la logique front
        'youtube_configured':   bool(cfg.youtube_rtmp),
        'tiktok_configured':    bool(cfg.tiktok_rtmp),
        'instagram_configured': bool(cfg.instagram_rtmp),
        'custom_configured':    bool(cfg.custom_rtmp),
        'video_quality': cfg.video_quality,
        'platforms': cfg.get_active_platforms(),
        'started_at': cfg.started_at.isoformat() if cfg.started_at else None,
        'viewers_count': cfg.viewers_count,
        'ffmpeg_available': bool(_find_ffmpeg()),
    })


@api_view(['POST'])
@permission_classes([IsDashboardOrAdmin])
def multistream_start(request):
    """Démarrer le relay FFmpeg vers toutes les plateformes."""
    cfg = _get_or_create_config()

    if cfg.status == 'live':
        return Response({'error': 'Un stream est déjà en cours.'}, status=400)

    ffmpeg_bin = _find_ffmpeg()
    if not ffmpeg_bin:
        return Response({
            'error': 'FFmpeg non trouvé sur ce serveur. Installez FFmpeg pour streamer depuis le navigateur.',
            'ffmpeg_missing': True,
        }, status=503)

    try:
        cmd = cfg.build_ffmpeg_cmd(ffmpeg_bin=ffmpeg_bin)
    except ValueError as e:
        return Response({'error': str(e)}, status=400)

    try:
        import tempfile, threading
        stderr_file = tempfile.NamedTemporaryFile(delete=False, suffix='.log', mode='wb')
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=stderr_file,
        )
        stderr_file.close()
        _FFMPEG_PROCS[cfg.pk] = proc
        _FFMPEG_PROCS[str(cfg.pk) + '_stderr'] = stderr_file.name
        cfg.status = 'live'
        cfg.ffmpeg_pid = proc.pid
        cfg.started_at = timezone.now()
        cfg.error_message = ''
        cfg.save()
        logger.info(f"FFmpeg démarré PID={proc.pid} pour config {cfg.pk}")
        return Response({'success': True, 'pid': proc.pid, 'platforms': cfg.get_active_platforms()})
    except Exception as e:
        cfg.status = 'error'
        cfg.error_message = str(e)
        cfg.save()
        logger.error(f"Erreur démarrage FFmpeg: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsDashboardOrAdmin])
def multistream_stop(request):
    """Arrêter le stream."""
    cfg = _get_or_create_config()
    proc = _FFMPEG_PROCS.pop(cfg.pk, None)
    stderr_log = _FFMPEG_PROCS.pop(str(cfg.pk) + '_stderr', None)
    if proc:
        try:
            proc.stdin.close()
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    elif cfg.ffmpeg_pid:
        try:
            os.kill(cfg.ffmpeg_pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
    if stderr_log:
        try:
            os.unlink(stderr_log)
        except Exception:
            pass

    cfg.status = 'idle'
    cfg.ffmpeg_pid = None
    cfg.stopped_at = timezone.now()
    cfg.save()

    # Marquer le LiveStream associé comme terminé
    LiveStream.objects.filter(status='live').update(status='ended')
    return Response({'success': True})


@api_view(['POST'])
@permission_classes([IsDashboardOrAdmin])
def multistream_ingest(request):
    """Recevoir un chunk WebM depuis le navigateur et le piper à FFmpeg."""
    cfg = _get_or_create_config()
    proc = _FFMPEG_PROCS.get(cfg.pk)

    if not proc or proc.poll() is not None:
        cfg.status = 'error'
        cfg.error_message = 'Processus FFmpeg inactif.'
        cfg.save()
        return Response({'error': 'FFmpeg inactif'}, status=400)

    chunk = request.body
    if chunk:
        try:
            proc.stdin.write(chunk)
            proc.stdin.flush()
        except (BrokenPipeError, OSError):
            stderr_log = _FFMPEG_PROCS.get(str(cfg.pk) + '_stderr', '')
            stderr_tail = ''
            if stderr_log:
                try:
                    with open(stderr_log, 'r', errors='replace') as f:
                        lines = f.readlines()
                        stderr_tail = ''.join(lines[-20:]).strip()
                except Exception:
                    pass
            cfg.status = 'error'
            cfg.error_message = stderr_tail or 'FFmpeg broken pipe.'
            cfg.save()
            logger.error(f"FFmpeg broken pipe. stderr: {stderr_tail}")
            return Response({'error': 'FFmpeg crash', 'ffmpeg_crash': True, 'stderr': stderr_tail}, status=500)

    return Response({'ok': True, 'bytes': len(chunk)})


@api_view(['GET'])
@permission_classes([IsDashboardOrAdmin])
def multistream_status(request):
    """Statut temps réel du stream."""
    cfg = _get_or_create_config()
    proc = _FFMPEG_PROCS.get(cfg.pk)

    # Vérifie si le processus est toujours vivant
    if cfg.status == 'live' and proc and proc.poll() is not None:
        cfg.status = 'error'
        cfg.error_message = 'FFmpeg s\'est arrêté inopinément.'
        cfg.save()

    duration = None
    if cfg.started_at and cfg.status == 'live':
        duration = int((timezone.now() - cfg.started_at).total_seconds())

    return Response({
        'status': cfg.status,
        'platforms': cfg.get_active_platforms(),
        'viewers_count': cfg.viewers_count,
        'duration': duration,
        'started_at': cfg.started_at.isoformat() if cfg.started_at else None,
        'error': cfg.error_message,
        'ffmpeg_alive': proc is not None and proc.poll() is None,
    })


# ── Events API ────────────────────────────────────────────────────────────────

def _parse_dt(val):
    """Parse ISO string or datetime-local value to datetime, accept datetime objects too."""
    if val is None:
        return None
    if hasattr(val, 'isoformat'):
        return val
    from django.utils.dateparse import parse_datetime
    from django.utils import timezone as tz
    parsed = parse_datetime(str(val))
    if parsed is None:
        return None
    if tz.is_naive(parsed):
        parsed = tz.make_aware(parsed)
    return parsed


def _fmt_dt(val):
    """Format datetime or string for JSON — never crashes."""
    if val is None:
        return None
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return str(val)


def _event_to_dict(e):
    return {
        'id':               e.id,
        'title':            e.title,
        'description':      e.description,
        'event_type':       e.event_type,
        'event_type_display': e.get_event_type_display(),
        'event_date':       _fmt_dt(e.event_date),
        'end_date':         _fmt_dt(e.end_date),
        'location':         e.location,
        'is_online':        e.is_online,
        'online_url':       e.online_url,
        'registration_url': e.registration_url,
        'is_published':     e.is_published,
        'is_featured':      e.is_featured,
        'status':           e.status,
        'image_url':        e.image.url if e.image else None,
    }


@api_view(['GET'])
@permission_classes([IsDashboardOrAdmin])
def events_api(request):
    events = Event.objects.all().order_by('event_date')
    return Response({'events': [_event_to_dict(e) for e in events], 'total': events.count()})


@api_view(['POST'])
@permission_classes([IsDashboardOrAdmin])
def event_create_api(request):
    try:
        data     = request.data
        ev_date  = _parse_dt(data.get('event_date'))
        end_date = _parse_dt(data.get('end_date'))
        if ev_date is None:
            return Response({'error': 'event_date invalide ou manquant'}, status=400)
        event = Event.objects.create(
            title            = (data.get('title') or '').strip(),
            description      = (data.get('description') or '').strip(),
            event_type       = data.get('event_type', 'autre'),
            event_date       = ev_date,
            end_date         = end_date,
            location         = (data.get('location') or '').strip(),
            is_online        = bool(data.get('is_online', False)),
            online_url       = (data.get('online_url') or '').strip(),
            registration_url = (data.get('registration_url') or '').strip(),
            is_published     = bool(data.get('is_published', True)),
            is_featured      = bool(data.get('is_featured', False)),
        )
        return Response({'success': True, 'id': event.id, 'event': _event_to_dict(event)}, status=201)
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsDashboardOrAdmin])
def event_update_api(request, pk):
    event = get_object_or_404(Event, pk=pk)
    data  = request.data
    if 'title'            in data: event.title            = (data['title'] or '').strip()
    if 'description'      in data: event.description      = (data['description'] or '').strip()
    if 'event_type'       in data: event.event_type       = data['event_type']
    if 'event_date'       in data: event.event_date       = _parse_dt(data['event_date']) or event.event_date
    if 'end_date'         in data: event.end_date         = _parse_dt(data['end_date'])
    if 'location'         in data: event.location         = (data['location'] or '').strip()
    if 'is_online'        in data: event.is_online        = bool(data['is_online'])
    if 'online_url'       in data: event.online_url       = (data['online_url'] or '').strip()
    if 'registration_url' in data: event.registration_url = (data['registration_url'] or '').strip()
    if 'is_published'     in data: event.is_published     = bool(data['is_published'])
    if 'is_featured'      in data: event.is_featured      = bool(data['is_featured'])
    event.save()
    return Response({'success': True, 'event': _event_to_dict(event)})


@api_view(['DELETE'])
@permission_classes([IsDashboardOrAdmin])
def event_delete_api(request, pk):
    event = get_object_or_404(Event, pk=pk)
    event.delete()
    return Response({'success': True})
