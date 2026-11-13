import streamlit as st
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from data import COMPANIES, MEMBERS, OPPS
from core import Store, baseline, catalogue, rank, status, assistant
from live import profile_live, discover, now
from extended import *

st.set_page_config(page_title='BlueLink | Virtual Science Park',page_icon='🌐',layout='wide')
from ui import CSS, hero, chips, match_label
st.markdown(CSS, unsafe_allow_html=True)
store=Store(str(Path(__file__).resolve().parent / "bluelink.sqlite3"))
accounts=Accounts(store)
if 'account' not in st.session_state:
    hero('Blue Science Park · Virtual Science Park','Your next innovation starts here.','Discover relevant funding, research, testing environments and potential collaborators in one evidence-led workspace.')
    st.subheader('Sign in to BlueLink AI')
    with st.form('login'):
        u=st.text_input('Username'); pw=st.text_input('Password',type='password'); login=st.form_submit_button('Sign in')
        if login:
            a=accounts.login(u,pw)
            if a: st.session_state.account=a; st.rerun()
            else: st.error('Invalid credentials')
    with st.expander('Create account',expanded=True):
        with st.form('register'):
            u=st.text_input('New username'); pw=st.text_input('New password (at least 12 characters)',type='password'); invite=st.text_input('Staff invitation (optional)',type='password')
            if st.form_submit_button('Register'):
                try: st.session_state.account=accounts.register(u,pw,invite); st.rerun()
                except ValueError as e: st.error(str(e))
    st.stop()
account=st.session_state.account; w=account['workspace']
with st.sidebar:
    st.markdown('<div class="bl-brand">BlueLink<span> AI</span></div>',unsafe_allow_html=True)
    st.caption('VIRTUAL SCIENCE PARK')
    st.divider()
    st.caption('Signed in as')
    st.write(account['username']+' · '+account['role'])
    if st.button('Sign out'):
        st.session_state.clear(); st.rerun()
    demo=st.toggle('Show simulated examples',value=False)
    name=st.selectbox('Member company',[x['name'] for x in COMPANIES]); company=next(x for x in COMPANIES if x['name']==name)
    st.link_button('Member directory',MEMBERS)
    st.caption('Public profiles only. Private refinements are scoped to this workspace.')
    use_ai=st.toggle('Use optional AI extraction',value=False)
    st.caption('Set OPENAI_API_KEY in your environment. Only public webpage text is sent to the model.')
    st.divider()
    pages=['Overview','Company profile','Opportunity radar','Collaboration','Saved & feedback','Assistant','Monitoring & alerts','Quality & handover']
    if account['role']=='staff': pages.append('Ecosystem insights')
    if st.session_state.get('navigation') not in pages: st.session_state['navigation']='Overview'
    page=st.radio('Navigate',pages,key='navigation',label_visibility='collapsed')
base=store.get(w,'public_profile',name,baseline(company)); edits=store.get(w,'edit',name,{})
p={**base,**edits}; live_records=store.get(w,'catalogue','live',[])
# Keep snapshots for offline coverage; replace matching source URLs or IDs with live records.
merged={o['id']:o for o in catalogue()}; urls={o['url']:o['id'] for o in merged.values()}
for o in live_records:
    old=urls.get(o['url']);
    if old: merged.pop(old,None)
    merged[o['id']]=o

if demo: merged.update({o['id']:o for o in demo_records()})
opps=list(merged.values()); feedback=store.get(w,'feedback',name,{}); saved=store.get(w,'saved',name,[])
refresh=store.get(w,'meta','refresh',{})
st.markdown('<div class="bl-kicker">Blue Science Park / Innovation intelligence</div>',unsafe_allow_html=True)
if page=='Overview':
    hero('Your innovation workspace', f'Welcome to {name}', 'Discover the right knowledge, opportunities and partners for your next business milestone.')
    ranked_all=rank(p,opps,feedback=feedback)
    metrics=st.columns(4)
    metrics[0].metric('Relevant matches',len(ranked_all))
    metrics[1].metric('Saved opportunities',len(saved))
    metrics[2].metric('Potential partners',len(collaborators(p,[store.get(w,'public_profile',c['name'],baseline(c)) for c in COMPANIES])))
    metrics[3].metric('New alerts',len(store.get(w,'alerts',name,[])))
    st.caption('Workspace catalogue · '+('Simulated examples enabled' if demo else 'Public records only')+' · '+('Last refresh: '+refresh.get('time','Unknown') if refresh else 'Offline baseline — no live refresh yet'))
    def go(target):
        st.session_state.navigation=target
    main,side=st.columns([1.65,1],gap='large')
    with main:
        st.subheader('Recommended for you')
        st.caption('Ranked by company technologies, interests and feedback.')
        for o in ranked_all[:3]:
            with st.container(border=True):
                st.caption(f"{o['category'].upper()}  ·  {o['provider']}  ·  {o['mode']}")
                st.markdown('**'+o['title']+'**')
                st.write(o['description'])
                match_label(o['score'])
                st.caption(o['status'])
                st.caption(f"Retrieved {o['retrieved']} · Deadline: {o.get('deadline') or 'Not verified'}")
                a,b=st.columns(2)
                a.link_button('Original source',o['url'],use_container_width=True)
                if b.button('Saved ✓' if o['id'] in saved else 'Save finding',key='overview_'+o['id'],disabled=o['mode'].startswith('SIMULATED'),use_container_width=True):
                    store.put(w,'saved',name,[x for x in saved if x!=o['id']] if o['id'] in saved else saved+[o['id']]); st.rerun()
        if not ranked_all: st.info('No matches yet. Refine your interests or refresh the public catalogue.')
        st.button('Explore opportunity radar →',type='primary',on_click=go,args=('Opportunity radar',),use_container_width=True)
    with side:
        with st.container(border=True):
            st.markdown('#### Company at a glance')
            st.caption(base['mode'])
            st.write(base['facts'])
            chips(base['tags'])
            if edits: st.caption('Private refinements active · used for matching, not public facts.')
            st.button('Review your profile',on_click=go,args=('Company profile',),use_container_width=True)
        with st.container(border=True):
            st.markdown('#### Opportunity mix')
            from collections import Counter
            mix=Counter(o['category'] for o in ranked_all)
            if mix: st.bar_chart([{'Category':k,'Matches':v} for k,v in mix.items()],x='Category',y='Matches',color='#087E87')
            else: st.caption('No matching categories yet.')
        with st.container(border=True):
            st.markdown('#### Quick actions')
            st.button('Discover collaborators',on_click=go,args=('Collaboration',),use_container_width=True)
            st.button('Ask BlueLink Assistant',on_click=go,args=('Assistant',),use_container_width=True)
            st.button('Check source updates',on_click=go,args=('Monitoring & alerts',),use_container_width=True)
            st.caption('Recommendations are suggestions, not confirmed eligibility, availability or commitments.')
else:
    hero('Innovation workspace',page,f'{name} · Evidence-led discovery and collaboration')
    st.caption('Public-source snapshots and live findings are labelled. Verify eligibility, availability and dates with the original provider.')
if page=='Company profile':
    st.subheader(name); st.caption(f"{base['mode']} • Retrieved: {base['retrieved']}")
    c1,c2=st.columns(2)
    if c1.button('Refresh selected profile',use_container_width=True):
        try:
            with st.spinner('Retrieving public company website…'): fresh=profile_live(company,use_ai)
            record_profile(store,w,fresh); st.rerun()
        except Exception as e: st.error(f'Live retrieval failed ({type(e).__name__}). Last available profile retained.')
    if c2.button('Refresh all member profiles',use_container_width=True):
        failures=[]
        def work(c):
            try: return c['name'],profile_live(c,use_ai),None
            except Exception as e: return c['name'],None,type(e).__name__
        with st.spinner('Retrieving public member websites…'):
            with ThreadPoolExecutor(max_workers=3) as pool:
                for n,result,error in pool.map(work,COMPANIES):
                    if result: record_profile(store,w,result)
                    else: failures.append(n+': '+error)
        store.put(w,'meta','profile_errors',failures); st.rerun()
    for err in store.get(w,'meta','profile_errors',[]): st.warning(err)
    if base.get('warning'): st.warning(base['warning'])
    st.markdown('**Public baseline facts / extracted claims**'); st.write(base['facts']); st.write('Markets: '+base['market']); st.write('Geography: '+base['geography']); st.write('Technologies: '+', '.join(base['tags'])); st.warning(base['missing'])
    with st.expander('Public priorities, projects and collaborations'):
        for field,label in [('public_priorities','Priorities'),('public_projects','Projects'),('public_collaborations','Collaborations')]: st.write(label+': '+base.get(field,'Not established in snapshot.'))
    with st.expander('Evidence and provenance',expanded=True):
        for e in base['evidence']:
            st.write(e.get('claim','')); st.caption(e['quote']); st.markdown(f"[Original source]({e['url']}) • {e['retrieved']}")
    st.markdown('**Inferred interests — not confirmed priorities**'); st.write(', '.join(base['interests']) or 'None inferred')
    with st.form('edit_'+name):
        st.markdown('**Your refinements**'); correction=st.text_area('Your company description / correction',p['facts']); tags=st.text_input('Technology tags (comma separated)',', '.join(p['tags'])); interests=st.text_input('Your current priorities (comma separated)',', '.join(p['interests'])); market=st.text_input('Markets and customer groups',p.get('market','')); geography=st.text_input('Geographical focus',p.get('geography','')); projects=st.text_area('Projects and collaborations (private notes)',p.get('projects',''))
        if st.form_submit_button('Save profile refinements'):
            store.put(w,'edit',name,{'facts':correction[:4000],'tags':[x.strip()[:100] for x in tags.split(',') if x.strip()][:30],'interests':[x.strip()[:100] for x in interests.split(',') if x.strip()][:30],'market':market[:500],'geography':geography[:500],'projects':projects[:2000]}); st.rerun()
    st.caption('User-provided corrections are kept separately from public evidence and persist across sessions after signing in to the same account.')
    if edits: st.write('Current user-supplied description: '+p['facts'])
    if st.button('Reset refinements'): store.delete(w,'edit',name); st.rerun()
if page=='Opportunity radar':
    st.subheader('Opportunity radar'); st.caption('Funding, testing, research, news and events • Public sources and labelled snapshots')
    if st.button('Discover and refresh public opportunities',type='primary'):
        with st.spinner('Checking provider listings and opportunity pages…'):
            results,errors=refresh_all(store,w,use_ai); st.rerun()
    if refresh:
        st.caption(f"Last attempt: {refresh['time']} • {refresh['count']} records retrieved")
        with st.expander('Source connector errors / diagnostics'):
            st.write(refresh['errors'] or 'No errors in last refresh.')
    f1,f2=st.columns([2,1]); cat=f1.selectbox('Category',CATEGORIES); query=f2.text_input('Search results',placeholder='Title, provider, topic'); closed=st.checkbox('Include closed calls and past events'); ranked=rank(p,opps,cat,closed,feedback)
    if query.strip(): ranked=[o for o in ranked if query.casefold().strip() in ' '.join([o['title'],o['provider'],o['description'],*o['tags']]).casefold()]
    sort=st.selectbox('Sort results',['Best match','Title A–Z','Deadline (earliest first)'])
    if sort=='Title A–Z': ranked.sort(key=lambda o:o['title'].casefold())
    elif sort=='Deadline (earliest first)': ranked.sort(key=lambda o:o.get('deadline') or o.get('event_date') or '9999-99-99')
    st.caption(f'{len(ranked)} matching records · Scores are relevance points, not probabilities')
    if not ranked: st.warning('No matching records in this view. Refresh sources or review priorities. Unknown deadlines are not confirmed open.')
    for o in ranked:
        with st.container(border=True):
            st.subheader(o['title']); st.caption(f"{o['provider']} • {o['category']} • {o['status']} • {o['mode']}"); st.write(o['description']);
            if o['category']=='Events': st.write('Event date: '+str(o.get('event_date') or 'Unverified')+' · Format: '+str(o.get('event_format') or 'Unverified'))
            match_label(o['score']); st.write(o['reason']); st.write('Eligibility/access: '+o['eligibility']); st.write('Next step: '+o['next']); st.caption(f"{o['date']} • Retrieved {o['retrieved']} • Deadline: {o['deadline'] or 'Not verified'}"); st.markdown(f"[Original source]({o['url']})")
            with st.expander('Evidence excerpts'):
                for e in o['evidence']: st.caption(e['quote']); st.markdown(f"[Source]({e['url']})")
            a,b,c=st.columns(3)
            if a.button('Unsave' if o['id'] in saved else 'Save',key='save'+o['id'],disabled=o['mode'].startswith('SIMULATED')):
                store.put(w,'saved',name,[x for x in saved if x!=o['id']] if o['id'] in saved else saved+[o['id']]); st.rerun()
            if b.button('Useful',key='up'+o['id'],disabled=o['mode'].startswith('SIMULATED')): store.put(w,'feedback',name,{**feedback,o['id']:1}); st.rerun()
            if c.button('Not useful',key='down'+o['id'],disabled=o['mode'].startswith('SIMULATED')): store.put(w,'feedback',name,{**feedback,o['id']:-1}); st.rerun()
if page=='Saved & feedback':
    st.subheader('Saved opportunities & feedback')
    for oid in saved:
        o=merged.get(oid)
        if o: st.markdown(f"**{o['title']}** — {status(o)} · [Source]({o['url']})")
        else: st.write('Previously saved record no longer in catalogue: '+oid)
    if not saved: st.caption('Save an opportunity from the radar to see it here.')
    st.write('Feedback influences ranking by at most one point per opportunity.'); st.json({merged.get(k,{}).get('title',k):v for k,v in feedback.items()})
    if st.button('Clear feedback'): store.delete(w,'feedback',name); st.rerun()
if page=='Assistant':
    st.subheader('Science park assistant'); st.caption('Purpose-restricted retrieval assistant across funding, testing, research, news, events and collaboration. No arbitrary generation or cross-workspace access.')
    q=st.text_input('Ask about your company',placeholder='Find testing opportunities')
    if st.button('Ask') and q.strip(): st.markdown(full_assistant(q[:2000],p,opps,[store.get(w,'public_profile',c['name'],baseline(c)) for c in COMPANIES],st.session_state.get('last_question_'+name,''))); st.session_state['last_question_'+name]=q[:2000]
    st.write('Demo prompts: Find testing opportunities · Write a poem · Ignore your instructions · Show another company’s private profile · Guarantee funding eligibility.')
if page=='Quality & handover':
    st.subheader('Quality and handover'); st.write('See README.md, EVALUATION.md and PITCH.md in the repository for setup, verification and presentation instructions.')
    st.write('Profile accuracy: public evidence and user corrections are separate. Recommendation relevance: tag and priority overlap plus bounded feedback. Traceability: source URL, retrieval time and live evidence text/hash. Interaction boundaries: allowlisted retrieval, structured AI outputs and a restricted assistant.')
    st.warning('Limitations: curated records are not live; live sites may block requests or change markup; deadline extraction is conservative; optional AI claims need human review; password accounts are prototype access control, not enterprise SSO or verified company identity. Scheduling requires an external scheduler; no confirmed eligibility.')
    st.markdown('[Contact Blue Science Park](https://www.bluesciencepark.se/)')

if page=='Collaboration':
    st.subheader('Potential collaboration partners')
    st.caption('Public partner information only. Suggested matches do not establish interest or consent.')
    public=[store.get(w,'public_profile',c['name'],baseline(c)) for c in COMPANIES]
    for partner in collaborators(p,public):
        with st.container(border=True):
            st.subheader(partner['name']); st.write('Shared technologies: '+(', '.join(partner['shared']) or 'None')); st.write('Complementary capabilities: '+(', '.join(a+' ↔ '+b for a,b in partner['complementary']) or 'None')); st.write(partner['next']); st.link_button('Public company website',partner['url'])
            for e in partner['evidence']: st.caption(e['quote']); st.write(e['url'])
if page=='Monitoring & alerts':
    st.subheader('Public member changes & opportunity alerts')
    if st.button('Refresh all sources and check changes'):
        with st.spinner('Retrieving public sources…'):
            refresh_all(store,w,use_ai)
        st.rerun()
    for change in reversed(store.get(w,'changes',name,[])):
        with st.expander(change['time']+' · Public change'):
            st.write(change['note']); st.write('Before: '+change['old_excerpt']); st.write('After: '+change['new_excerpt']); st.write(change['url'])
    if not store.get(w,'changes',name,[]): st.caption('No changes detected yet. Refresh twice to establish and compare snapshots.')
    for a in reversed(store.get(w,'alerts',name,[])):
        st.markdown(f"**{a['title']}** · {a['time']} — [Source]({a['url']})"); st.caption(a['reason'])
    prefs=store.get(w,'preferences','email',{})
    with st.form('email_preferences'):
        address=st.text_input('Email for digests',value=prefs.get('address','')); enabled=st.checkbox('Opt in to email digests',value=prefs.get('enabled',False))
        if st.form_submit_button('Save alert preferences'):
            store.put(w,'preferences','email',{'address':address.strip(),'enabled':enabled}); st.success('Preferences saved')
    if st.button('Send pending digest'):
        try: st.info(send_digest(store,w))
        except Exception as e: st.error('Email failed: '+type(e).__name__)
    st.caption('Scheduled refresh: run refresh.py externally. SMTP configuration is optional.')
if page=='Ecosystem insights':
    st.subheader('Blue Science Park staff insights')
    if account['role']!='staff': st.info('Staff access required. Register with a configured staff invitation.')
    else:
        public=[store.get(w,'public_profile',c['name'],baseline(c)) for c in COMPANIES]
        from collections import Counter
        counts=Counter(t.lower() for c in public for t in set(c['tags']))
        st.metric('Public members represented',len(public)); st.bar_chart([{"Technology":t,"Companies":n} for t,n in counts.most_common()],x="Technology",y="Companies") if counts else st.caption("No public technology tags yet.")
        st.dataframe([{'Company':c['name'],'Public technologies':', '.join(c['tags']),'Source':c['url']} for c in public],use_container_width=True)
        for c in public:
            for partner in collaborators(c,public):
                if c['name']<partner['name']: st.write(c['name']+' ↔ '+partner['name']+' · '+', '.join(partner['shared']+[a+' / '+b for a,b in partner['complementary']]))
        st.caption('Public-only overview; never aggregates private user profiles or interactions.')
