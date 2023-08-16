async function postNotificationPreference(acceptsNotifications, notificationSettingUrl) {
  // Post notification setting to form.
  let post_url = notificationSettingUrl;
  let formData = new FormData();

  formData.append("accepts_notifications", acceptsNotifications);
  formData.append("csrfmiddlewaretoken", Cookies.get("csrftoken"));
  const response = await fetch(post_url, {
    method: "POST",
    body: formData,
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  });
  return response;
}

async function setPushPreference(webPushAction, notificationSettingUrl) {
  // Subscribe or unsubscribe to browser notification service, then ask for browser permission to notify, then set owner attribute.
  let wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  const notificationsPreferenceTips = document.querySelector("#notifications-preference-tips");
  const notificationsSpinner = document.querySelector("#notifications-spinner");

  notificationsSpinner.classList.toggle("d-none");
  webPushAction(registration);
  await wait(1000);
  let subscription = await registration.pushManager.getSubscription();
  let subscriptionFailed = true;
  let acceptsNotifications = false;
  let errorMessage = gettext("Error");
  if (webPushAction == subscribe) {
    subscriptionFailed = subscription === null || Notification.permission !== "granted";
    acceptsNotifications = true
    errorMessage = gettext("Don't forget to allow notifications from this website in your browser's settings!");
  } else if (webPushAction == unsubscribe) {
    subscriptionFailed = subscription !== null;
    acceptsNotifications = false
    errorMessage = gettext("Error during unsubscription...");
  }

  if (subscriptionFailed) {
    notificationsPreferenceTips.classList.remove("d-none");
    notificationsPreferenceTips.textContent = errorMessage;
    notificationsSpinner.classList.toggle("d-none");
  } else {
    const preferenceResponse = await postNotificationPreference(acceptsNotifications, notificationSettingUrl);
    if (!preferenceResponse.ok) {
      notificationsPreferenceTips.classList.remove("d-none");
      notificationsPreferenceTips.textContent = errorMessage;
      notificationsSpinner.classList.toggle("d-none");
    } else {
      if (!("d-none" in notificationsPreferenceTips.classList)) notificationsPreferenceTips.classList.add("d-none");
      await wait(500);
      notificationsSpinner.classList.toggle("d-none");
      new bootstrap.Toast(document.querySelector('#notification-toast')).hide();
    }
  }
}
