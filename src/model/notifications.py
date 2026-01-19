from flask import Blueprint, jsonify, session
from src.model.db.database import get_connection
from src.model.Notification import Notification
import json

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/api/notifications')
def get_notifications():
    """Get notifications using existing database connection"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    user_id = session['user_id']
    role = session.get('role', 'patient')

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if role in ['admin', 'doctor']:
            # Admin/Doctor can see all notifications with user info
            cursor.execute('''
                           SELECT n.*, u.email, u.role
                           FROM notification n
                                    JOIN user u ON n.user_id = u.id
                           ORDER BY n.timestamp DESC
                           LIMIT 20
                           ''')
        else:
            # Patients only see their own notifications
            cursor.execute('''
                           SELECT * FROM notification
                           WHERE user_id = ?
                           ORDER BY timestamp DESC
                           LIMIT 20
                           ''', (user_id,))

        notifications = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@notifications_bp.route('/api/notifications/create', methods=['POST'])
def create_notification():
    """Create a notification for a user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    data = request.json
    target_user_id = data.get('user_id')
    message = data.get('message')
    title = data.get('title', 'System Notification')

    # Only admin/doctor can create notifications for others
    if session['role'] not in ['admin', 'doctor'] and target_user_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Not authorized'}), 403

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
                       INSERT INTO notification (user_id, title, message, timestamp)
                       VALUES (?, ?, ?, NOW())
                       ''', (target_user_id, title, message))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Notification created'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@notifications_bp.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Delete a notification"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check ownership
        cursor.execute('SELECT user_id FROM notification WHERE id = ?', (notification_id,))
        notification = cursor.fetchone()

        if not notification:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Notification not found'}), 404

        # Only owner or admin/doctor can delete
        if session['role'] not in ['admin', 'doctor'] and notification[0] != session['user_id']:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Not authorized'}), 403

        # Delete notification
        cursor.execute('DELETE FROM notification WHERE id = ?', (notification_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Notification deleted'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500