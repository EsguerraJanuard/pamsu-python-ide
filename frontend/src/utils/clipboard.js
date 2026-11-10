/**
 * Copy text to the clipboard. Tries the Clipboard API first; where that is
 * missing or refused (plain http, an embedded browser, no permission), falls
 * back to the older copy command on a temporary hidden textarea. Focus goes
 * back to where it was. Resolves to true when the text was copied.
 */
export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fall through to the copy command below.
  }
  const previous = document.activeElement;
  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.top = "0";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  let copied;
  try {
    copied = document.execCommand("copy");
  } catch {
    copied = false;
  }
  area.remove();
  previous?.focus?.({ preventScroll: true });
  return copied;
}
