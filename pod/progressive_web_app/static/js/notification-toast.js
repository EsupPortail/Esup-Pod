var notificationToast = document.querySelector("#notification-toast");
notificationToast.addEventListener("shown.bs.toast", updateToast);

async function postNotificationPreference(
  acceptsNotifications,
  notificationSettingUrl,
) {
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

async function setPushPreference(notificationSettingUrl) {
  const notificationsSpinner = document.querySelector("#notifications-spinner");
  const notificationButton = document.querySelector(
    "#notification-action-button",
  );
  const notificationsPreferenceTips = document.querySelector(
    "#notifications-preference-tips",
  );

  notificationsSpinner.classList.remove("d-none");
  notificationButton.disabled = true;

  let afterBrowserNotificationPermissionChanged = async function (
    subscription,
  ) {
    acceptsNotifications = subscription != null;
    let response = await postNotificationPreference(
      acceptsNotifications,
      notificationSettingUrl,
    );

    await updateToast();

    if (!response.ok) {
      notificationsPreferenceTips.textContent = gettext(
        "An error happened during notification subscription",
      );
      notificationsPreferenceTips.classList.remove("alert-primary");
      notificationsPreferenceTips.classList.remove("alert-warning");
      notificationsPreferenceTips.classList.add("alert-error");
    }
  };

  let permissionState = await registration.pushManager.permissionState({
    userVisibleOnly: true,
  });
  let subscription = await registration.pushManager.getSubscription();

  if (permissionState == "prompt") {
    notificationsPreferenceTips.classList.remove("d-none");
    notificationsPreferenceTips.classList.remove("alert-primary");
    notificationsPreferenceTips.classList.remove("alert-error");
    notificationsPreferenceTips.classList.add("alert-warning");
    notificationsPreferenceTips.textContent = gettext(
      "Don't forget to allow notifications from this website in your browser's settings!",
    );

    subscribe(registration, afterBrowserNotificationPermissionChanged);
  } else if (permissionState == "granted" && !subscription) {
    subscribe(registration, afterBrowserNotificationPermissionChanged);
  } else if (permissionState == "granted" && subscription) {
    subscription.unsubscribe().then(() => {
      afterBrowserNotificationPermissionChanged(subscription);
    });
  }
}

async function updateToast() {
  const notificationButton = document.querySelector(
    "#notification-action-button",
  );
  const notificationsPreferenceTips = document.querySelector(
    "#notifications-preference-tips",
  );
  const notificationsSpinner = document.querySelector("#notifications-spinner");

  notificationsSpinner.classList.add("d-none");

  let permissionState = await registration.pushManager.permissionState({
    userVisibleOnly: true,
  });
  let subscription = await registration.pushManager.getSubscription();

  if (permissionState == "denied") {
    notificationsPreferenceTips.classList.remove("d-none");
    notificationsPreferenceTips.classList.remove("alert-primary");
    notificationsPreferenceTips.classList.remove("alert-warning");
    notificationsPreferenceTips.classList.add("alert-error");
    notificationsPreferenceTips.textContent = gettext(
      "You have denied notifications in your browser, to enable them back you must do it in your browser configuration menu.",
    );
    notificationButton.textContent = gettext("Enable notifications");
    notificationButton.disabled = true;
  } else if (
    permissionState == "prompt" ||
    (permissionState == "granted" && !subscription)
  ) {
    notificationsPreferenceTips.classList.remove("d-none");
    notificationsPreferenceTips.classList.remove("alert-primary");
    notificationsPreferenceTips.classList.remove("alert-warning");
    notificationsPreferenceTips.classList.add("alert-warning");
    notificationsPreferenceTips.textContent = gettext(
      "Notifications are currently disabled.",
    );
    notificationButton.textContent = gettext("Enable notifications");
    notificationButton.disabled = false;
  } else if (permissionState == "granted") {
    notificationsPreferenceTips.classList.remove("d-none");
    notificationsPreferenceTips.classList.remove("alert-error");
    notificationsPreferenceTips.classList.remove("alert-warning");
    notificationsPreferenceTips.classList.add("alert-primary");
    notificationsPreferenceTips.textContent = gettext(
      "Notifications are currently enabled.",
    );
    notificationButton.textContent = gettext("Disable notifications");
    notificationButton.disabled = false;
  }
}

// This function is an adaptation of
// https://github.com/safwanrahman/django-webpush/blob/0561306f133619297d7d66dd683690edf55cf325/webpush/static/webpush/webpush.js#L92-L132
// The only change is the addition of the callback parameter and its call on success
// It can be removed when the following feature is implemented:
// https://github.com/safwanrahman/django-webpush/issues/133
function subscribe(reg, callback = null) {
  // Get the Subscription or register one
  reg.pushManager.getSubscription().then(function (subscription) {
    var metaObj, applicationServerKey, options;
    // Check if Subscription is available
    if (subscription) {
      return subscription;
    }

    metaObj = document.querySelector('meta[name="django-webpush-vapid-key"]');
    applicationServerKey = metaObj.content;
    options = {
      userVisibleOnly: true,
    };
    if (applicationServerKey) {
      options.applicationServerKey = urlB64ToUint8Array(applicationServerKey);
    }
    // If not, register one
    reg.pushManager
      .subscribe(options)
      .then(function (subscription) {
        postSubscribeObj("subscribe", subscription, function (response) {
          // Check the information is saved successfully into server
          if (response.status === 201) {
            // Show unsubscribe button instead
            subBtn.textContent = gettext("Unsubscribe from Push Messaging");
            subBtn.disabled = false;
            isPushEnabled = true;
            showMessage(
              gettext("Successfully subscribed to push notifications."),
            );
          }
        });
        if (callback) {
          callback(subscription);
        }
      })
      .catch(function () {
        console.log(
          gettext("Error while subscribing to push notifications."),
          arguments,
        );
        if (callback) {
          callback(null);
        }
      });
  });
}
