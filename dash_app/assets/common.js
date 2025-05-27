(function () {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    localStorage.setItem("userTimezone", tz);
})();