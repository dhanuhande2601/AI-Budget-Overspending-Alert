// =========================================
// Browser Push Notification Helper
// =========================================
 
export function isNotificationSupported() {
  return 'Notification' in window
}
 
export function getNotificationPermission() {
  if (!isNotificationSupported()) return 'unsupported'
  return Notification.permission   // 'granted' | 'denied' | 'default'
}
 
export async function requestNotificationPermission() {
  if (!isNotificationSupported()) return 'unsupported'
 
  if (Notification.permission === 'granted') return 'granted'
  if (Notification.permission === 'denied') return 'denied'
 
  const result = await Notification.requestPermission()
  return result
}
 
export function showBudgetNotification(title, body, tag) {
  if (!isNotificationSupported()) return
  if (Notification.permission !== 'granted') return
 
  // tag prevents duplicate notifications for the same alert type
  const notification = new Notification(title, {
    body,
    icon: '/favicon.svg',
    tag,
    requireInteraction: false,
  })
 
  notification.onclick = () => {
    window.focus()
    notification.close()
  }
 
  // Auto close after 8 seconds
  setTimeout(() => notification.close(), 8000)
}