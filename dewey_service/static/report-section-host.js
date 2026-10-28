// Called inside the trusted shell after its exact preview origin is established.
function retainReportSections(origin, firstFrame, reportError, hideNotice, status) {
  const frames = new Map();
  let active = firstFrame, pending = null, sequence = 0;
  // MultiQC carries scientific selector state in the fragment. Distinct
  // filters require distinct initialized views; output anchors do not.
  const key = url => url.pathname + url.search + '\u0000' +
    (url.hash.startsWith('#mqc-state=') ? new URLSearchParams(url.hash.slice(1)).get('mqc-state') : '');
  const parse = value => {
    const url = new URL(value);
    if (url.origin !== origin || url.username || url.password ||
        !url.pathname.startsWith('/__dewey_preview/assets/') || !/\.html?$/i.test(url.pathname))
      throw new Error('Invalid report section location');
    return url;
  };
  const fail = error => {
    for (const frame of new Set([firstFrame, ...frames.values()])) frame.remove();
    pending = null; reportError(error);
  };
  const show = (frame, url) => {
    active.hidden = true; frame.hidden = false; active = frame; pending = null;
    frame.contentWindow.postMessage({type:'dewey-section-visible', hash:url.hash}, origin);
    hideNotice();
  };
  const create = url => {
    const frame = document.createElement('iframe');
    frame.title = 'Shared report section';
    frame.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-downloads');
    frame.referrerPolicy = 'no-referrer';
    active.hidden = true; active = frame;
    frame.addEventListener('load', () => {
      if (pending?.frame === frame) pending = null;
    });
    frame.src = url.href; frames.set(key(url), frame); document.body.append(frame);
    pending = {frame, url, sequence:++sequence};
  };
  window.addEventListener('message', event => {
    if (event.origin !== origin) return;
    const source = [firstFrame, ...frames.values()].find(frame => frame.contentWindow === event.source);
    if (!source) return;
    const message = event.data;
    try {
      if (message?.type === 'dewey-section-ready') {
        const url = parse(message.href);
        frames.set(key(url), source);
        if (pending?.frame === source) show(source, pending.url);
        else if (source === active) hideNotice();
      } else if (message?.type === 'dewey-section-navigate' && source === active) {
        if (pending) return;
        const url = parse(message.href), current = parse(message.currentHref);
        for (const [oldKey, frame] of frames) if (frame === source) frames.delete(oldKey);
        frames.set(key(current), source);
        const cached = frames.get(key(url));
        status.textContent = 'Opening report section…';
        document.getElementById('report-notice').hidden = false;
        if (cached) {
          pending = {frame:cached, url, sequence:++sequence};
          cached.contentWindow.postMessage({type:'dewey-section-activate', sequence}, origin);
        } else create(url);
      } else if (pending?.frame === source && message?.sequence === pending.sequence) {
        if (message.type === 'dewey-section-authorized') show(source, pending.url);
        else if (message.type === 'dewey-section-changed') {
          const url = pending.url;
          for (const [oldKey, frame] of frames) if (frame === source) frames.delete(oldKey);
          source.remove(); create(url);
        } else if (message.type === 'dewey-section-error') fail(new Error(message.message));
      }
    } catch (error) { fail(error); }
  });
}
