import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

// Configurar comportamento das notificações
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export class NotificationService {
  static async requestPermissions(): Promise<boolean> {
    try {
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        console.warn('Permissão para notificações negada');
        return false;
      }

      // Configurar canal de notificação para Android
      if (Platform.OS === 'android') {
        await Notifications.setNotificationChannelAsync('default', {
          name: 'Escalator',
          importance: Notifications.AndroidImportance.MAX,
          vibrationPattern: [0, 250, 250, 250],
          lightColor: '#2563eb',
        });
      }

      return true;
    } catch (error) {
      console.error('Erro ao solicitar permissões de notificação:', error);
      return false;
    }
  }

  static async schedulePointReminder(title: string, body: string, triggerDate: Date): Promise<string | null> {
    try {
      const hasPermission = await this.requestPermissions();
      if (!hasPermission) {
        return null;
      }

      const notificationId = await Notifications.scheduleNotificationAsync({
        content: {
          title,
          body,
          sound: 'default',
          priority: Notifications.AndroidNotificationPriority.HIGH,
        },
        trigger: {
          date: triggerDate,
        },
      });

      return notificationId;
    } catch (error) {
      console.error('Erro ao agendar notificação:', error);
      return null;
    }
  }

  static async scheduleBreakReminder(): Promise<string | null> {
    const now = new Date();
    const breakTime = new Date(now.getTime() + 4 * 60 * 60 * 1000); // 4 horas depois

    return this.schedulePointReminder(
      '⏰ Lembrete de Pausa',
      'Não se esqueça de registrar sua pausa para o almoço!',
      breakTime
    );
  }

  static async scheduleEndOfDayReminder(): Promise<string | null> {
    const now = new Date();
    const endTime = new Date(now.getTime() + 8 * 60 * 60 * 1000); // 8 horas depois

    return this.schedulePointReminder(
      '🏁 Fim do Expediente',
      'Hora de registrar sua saída! Tenha um ótimo resto do dia.',
      endTime
    );
  }

  static async showImmediateNotification(title: string, body: string): Promise<void> {
    try {
      const hasPermission = await this.requestPermissions();
      if (!hasPermission) {
        return;
      }

      await Notifications.presentNotificationAsync({
        title,
        body,
        sound: 'default',
        priority: Notifications.AndroidNotificationPriority.HIGH,
      });
    } catch (error) {
      console.error('Erro ao mostrar notificação imediata:', error);
    }
  }

  static async cancelNotification(notificationId: string): Promise<void> {
    try {
      await Notifications.cancelScheduledNotificationAsync(notificationId);
    } catch (error) {
      console.error('Erro ao cancelar notificação:', error);
    }
  }

  static async cancelAllNotifications(): Promise<void> {
    try {
      await Notifications.cancelAllScheduledNotificationsAsync();
    } catch (error) {
      console.error('Erro ao cancelar todas as notificações:', error);
    }
  }

  static async getPendingNotifications(): Promise<Notifications.NotificationRequest[]> {
    try {
      return await Notifications.getAllScheduledNotificationsAsync();
    } catch (error) {
      console.error('Erro ao obter notificações pendentes:', error);
      return [];
    }
  }
}

// Tipos de notificações predefinidas
export const NotificationTypes = {
  POINT_REMINDER: 'point_reminder',
  BREAK_REMINDER: 'break_reminder',
  END_DAY_REMINDER: 'end_day_reminder',
  SCHEDULE_UPDATE: 'schedule_update',
  OVERTIME_ALERT: 'overtime_alert',
} as const;

export type NotificationType = typeof NotificationTypes[keyof typeof NotificationTypes];