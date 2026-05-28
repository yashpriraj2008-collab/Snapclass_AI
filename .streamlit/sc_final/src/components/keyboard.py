import streamlit as st
import streamlit.components.v1 as components


def enable_enter_to_next_input():
    """
    Makes Enter key move focus to next input/select/textarea/button.
    Useful for login/register forms.
    """
    components.html(
        """
        <html>
          <head>
            <style>
              html, body {
                margin: 0;
                padding: 0;
                width: 1px;
                height: 1px;
                overflow: hidden;
                background: transparent;
              }
            </style>
          </head>
          <body>
            <script>
            const doc = window.parent.document;

            function enableEnterToNext() {
                const focusableSelectors = [
                    'input:not([type="hidden"])',
                    'textarea',
                    'select',
                    'button'
                ];

                const elements = Array.from(
                    doc.querySelectorAll(focusableSelectors.join(','))
                ).filter(el => {
                    const style = window.parent.getComputedStyle(el);
                    return (
                        !el.disabled &&
                        el.offsetParent !== null &&
                        style.display !== 'none' &&
                        style.visibility !== 'hidden'
                    );
                });

                elements.forEach((el, index) => {
                    if (el.dataset.enterNextAttached === "true") return;

                    el.dataset.enterNextAttached = "true";

                    el.addEventListener("keydown", function(event) {
                        if (event.key === "Enter") {
                            const tag = el.tagName.toLowerCase();

                            if (tag === "textarea") return;

                            event.preventDefault();

                            const next = elements[index + 1];

                            if (next) {
                                next.focus();
                            } else {
                                el.blur();
                            }
                        }
                    });
                });
            }

            enableEnterToNext();

            const observer = new MutationObserver(enableEnterToNext);
            observer.observe(doc.body, {
                childList: true,
                subtree: true
            });
            </script>
          </body>
        </html>
        """,
        height=1,
        width=1,
        scrolling=False,
    )
