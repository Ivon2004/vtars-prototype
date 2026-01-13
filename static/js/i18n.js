/* Simple client-side i18n for VTARS (en / sw)
 - Stores selection in localStorage 'vtars_lang'
 - Also reads '?lang=xx' query param to allow linking
 - Translates elements with data-i18n (text content) and data-i18n-placeholder (input placeholders)
*/
(function(){
  const LANG_KEY = 'vtars_lang';
  const supported = ['en','sw'];
  const defaultLang = 'en';

  function getQueryLang(){
    try{
      const params = new URLSearchParams(window.location.search);
      const v = params.get('lang');
      return v && supported.includes(v) ? v : null;
    }catch(e){return null}
  }

  const dict = {
    en: {
      brand: 'VTARS',
      home: 'Home',
      dashboard: 'Dashboard',
      portals: 'Portals',
      logout: 'Logout',
      admin_portal: 'Admin Portal',
      student_portal: 'Student Portal',
      trainer_portal: 'Trainer Portal',
      admin_login: 'Admin Login',
      username: 'Username',
      password: 'Password',
      login: 'Login',
      general_user_login: 'General User Login',
      portals_title: 'VTARS Portals',
      daily_qr: 'Daily QR Code',
      print_qr: 'Print or display this QR at the entrance.',
      todays_attendance: "Today's attendance:",
      trainers: 'Trainers',
      students: 'Students',
      export_report: "Export Today's Report (CSV)",
      view_dashboard: 'View Dashboard',
      welcome_dashboard: 'Welcome to VTARS Dashboard',
      hello: 'Hello',
      todays_count: "Today's Attendance Count:",
      generate_reports: 'Generate Daily QR & View Reports',
      reported_status: 'Your reporting status today:',
      scan_attendance: 'Scan Attendance',
      scan_qr: 'Scan Attendance QR',
      back_to_dashboard: 'Back to Dashboard'
    },
    sw: {
      brand: 'VTARS',
      home: 'Nyumbani',
      dashboard: 'Dashibodi',
      portals: 'Vituo',
      logout: 'Toka',
      admin_portal: 'Kitovu cha Msimamizi',
      student_portal: 'Kitovu cha Mwanafunzi',
      trainer_portal: 'Kitovu cha Mwalimu',
      admin_login: 'Ingia Msimamizi',
      username: 'Jina la mtumiaji',
      password: 'Nenosiri',
      login: 'Ingia',
      general_user_login: 'Ingia Mtumiaji Mkweli',
      portals_title: 'Vituo vya VTARS',
      daily_qr: 'QR ya Kila Siku',
      print_qr: 'Chapisha au onyesha QR hii mlango.',
      todays_attendance: 'Mahudhurio ya leo:',
      trainers: 'Wafundishaji',
      students: 'Wanafunzi',
      export_report: 'Hamisha Ripoti ya Leo (CSV)',
      view_dashboard: 'Angalia Dashibodi',
      welcome_dashboard: 'Karibu kwenye Dashibodi ya VTARS',
      hello: 'Habari',
      todays_count: 'Idadi ya Mahudhurio ya Leo:',
      generate_reports: 'Tengeneza QR ya Kila Siku & Tazama Ripoti',
      reported_status: 'Hali yako ya kuripoti leo:',
      scan_attendance: 'Piga Mahudhurio',
      scan_qr: 'Soma QR ya Mahudhurio',
      back_to_dashboard: 'Rudi kwenye Dashibodi'
    }
  };

  function setLang(lang){
    if(!supported.includes(lang)) lang = defaultLang;
    localStorage.setItem(LANG_KEY, lang);
    applyTranslations(lang);
    // update language selector active state
    const btns = document.querySelectorAll('[data-lang-toggle]');
    btns.forEach(b=>{
      if(b.dataset.langToggle === lang) b.classList.add('active-lang'); else b.classList.remove('active-lang');
    })
  }

  function applyTranslations(lang){
    const tr = dict[lang] || dict[defaultLang];
    // text nodes
    document.querySelectorAll('[data-i18n]').forEach(el=>{
      const key = el.dataset.i18n;
      if(!key) return;
      if(tr[key]) el.textContent = tr[key];
    });
    // placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el=>{
      const key = el.dataset.i18nPlaceholder;
      if(!key) return;
      if(tr[key]) el.setAttribute('placeholder', tr[key]);
    });
    // option elements (e.g., role select)
    document.querySelectorAll('[data-i18n-option]').forEach(el=>{
      const map = JSON.parse(el.dataset.i18nOption);
      // map should be like {"student":"student_portal"} etc but here we expect a mapping of value->key
      for(const [val,key] of Object.entries(map)){
        const opt = el.querySelector(`option[value="${val}"]`);
        if(opt && tr[key]) opt.textContent = tr[key];
      }
    });
  }

  // initialize on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', ()=>{
    const qLang = getQueryLang();
    const stored = localStorage.getItem(LANG_KEY);
    const start = qLang || (supported.includes(stored) ? stored : defaultLang);
    // attach click handlers to toggles
    document.querySelectorAll('[data-lang-toggle]').forEach(btn=>{
      btn.addEventListener('click', (e)=>{
        e.preventDefault();
        const l = btn.dataset.langToggle;
        setLang(l);
        // update URL param without reloading
        const url = new URL(window.location.href);
        url.searchParams.set('lang', l);
        history.replaceState(null, '', url.toString());
      })
    });

    setLang(start);
  });
})();