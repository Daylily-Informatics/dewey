/* Runs only on the isolated report origin, never the Dewey application origin. */
(() => {
  const config = __DEWEY_SECTION_CONFIG__;
  const send = (data) => parent.postMessage(data, config.applicationOrigin);
  window.addEventListener('load', () => {
    if (!window.MQCBundle || !document.querySelector('a[data-bundle-nav]')) return;
    send({type:'dewey-section-ready', href:location.href});
    document.addEventListener('click', event => {
      const link = event.target.closest('a[data-bundle-nav]');
      if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey ||
          event.altKey || link.download || (link.target && link.target !== '_self')) return;
      const url = new URL(link.href);
      if (url.origin !== location.origin || !url.pathname.startsWith('/__dewey_preview/assets/') ||
          !/\.html?$/i.test(url.pathname) ||
          (url.pathname === location.pathname && url.search === location.search)) return;
      event.preventDefault(); event.stopImmediatePropagation();
      send({type:'dewey-section-navigate', href:url.href, currentHref:location.href});
    }, true);
    window.addEventListener('message', async event => {
      if (event.source !== parent || event.origin !== config.applicationOrigin ||
          event.data?.type !== 'dewey-section-activate') return;
      const sequence = event.data.sequence;
      try {
        // Reuse rendered state only after the normal live authorization and
        // provider conditional request say the selected document is unchanged.
        const response = await fetch(location.href, {method:'HEAD', credentials:'same-origin',
          cache:'no-store', headers:{'If-None-Match':config.etag}});
        if (response.status === 304) {
          send({type:'dewey-section-authorized', sequence});
        } else if (response.ok) {
          send({type:'dewey-section-changed', sequence});
        } else {
          throw new Error('Report access failed (' + response.status + '). Reopen the report to sign in again.');
        }
      } catch (error) { send({type:'dewey-section-error', sequence, message:error.message}); }
    });
    window.addEventListener('message', event => {
      if (event.source !== parent || event.origin !== config.applicationOrigin ||
          event.data?.type !== 'dewey-section-visible') return;
      if (event.data.hash) location.hash = event.data.hash;
      window.dispatchEvent(new Event('resize'));
    });
  }, {once:true});
})();
