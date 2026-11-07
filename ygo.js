/*! ygo.js: the light and the dark theme of ygo.css. https://github.com/tsoj/ygo.css

    Load it in <head>, before the page is drawn: <script src="ygo.css/ygo.js"></script>.
    The theme is light unless dark was chosen; the choice is stored (localStorage "ygo-theme").
    Any element with the class ygo-theme-toggle switches the theme when clicked, e.g.
    <button class="attribute ygo-theme-toggle" type="button" aria-label="Light / dark theme">. */

(function () {
    var root = document.documentElement;
    var KEY = 'ygo-theme';

    function apply(theme) {
        if (theme === 'dark') root.setAttribute('data-theme', 'dark');
        else root.removeAttribute('data-theme');
    }

    try { apply(localStorage.getItem(KEY)); } catch (e) {}

    window.ygoToggleTheme = function () {
        var theme = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        apply(theme);
        try {
            if (theme === 'dark') localStorage.setItem(KEY, 'dark');
            else localStorage.removeItem(KEY);
        } catch (e) {}
    };

    document.addEventListener('click', function (event) {
        if (event.target.closest && event.target.closest('.ygo-theme-toggle')) window.ygoToggleTheme();
    });
})();
