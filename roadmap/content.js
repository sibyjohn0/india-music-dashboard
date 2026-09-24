/* Indie Music India · Roadmap workbook content.
   Faithful digital version of the "Artist Workbook".
   Self-serve adaptations from the cohort original: action-item wrapper renamed
   "Your action items" (dropped "before the next session"), "Session notes" ->
   "Your notes", and a few cohort-only lines reframed for a solo artist.
   Edit freely · the engine in index.html renders whatever is here. */
window.WORKBOOK = {
  pillars: [
    "Identity & brand clarity",
    "Production consistency and quality",
    "Distribution and discoverability",
    "Rights and publishing literacy",
    "Revenue diversity",
    "Social media presence",
    "Live performance and networking",
    "Team and infrastructure"
  ],

  sections: [
    /* 0 · START HERE ------------------------------------------------------ */
    {
      id: "start", name: "Start here", tag: "How this works, and your honest starting point.",
      plain: "Two things before you dive in: understand how to use this, and rate where you are today. Be honest here, it makes everything after it work.",
      blocks: [
        { type:"info", title:"How to use this workbook", body:[
          "Work through one section at a time. You don't have to finish it in one sitting, everything saves as you go.",
          "Fill things in as you decide them, not 'later'. A rough answer you can improve beats a blank you never return to.",
          "The action items in each section are the minimum you commit to before moving on.",
          "Come back and change earlier answers as you grow. Your identity, your plan, your numbers, all of it will shift. That's the point."
        ]},
        { type:"pillars", id:"baseline", title:"Your baseline self-assessment",
          help:"Rate yourself 1–10 on each pillar, then note your biggest strength and biggest gap. This is your 'before' picture. You'll compare against it at the end." },
        { type:"fill", id:"baseline_top", title:"Sum it up", items:[
          {id:"strengths3", label:"My top 3 strengths right now", ph:"e.g. melodies, consistency, my live energy", long:true},
          {id:"gaps3", label:"My top 3 gaps right now", ph:"e.g. distribution, no press, no email list", long:true},
          {id:"goal1", label:"My single most important goal for this programme", ph:"One clear goal", long:true}
        ]},
        { type:"checklist", id:"start_actions", title:"Your action items", items:[
          {id:"a_baseline", text:"Complete the baseline self-assessment above"},
          {id:"a_bio", text:"Write a 2-sentence artist bio you can share anywhere"},
          {id:"a_goals", text:"Set 3 goals for the next 12 weeks and write them down"},
          {id:"a_intro", text:"Share your bio in one community or group you're part of"}
        ]},
        { type:"note", id:"start_notes" }
      ]
    },

    /* 1 · CONTEXT & DIAGNOSTIC -------------------------------------------- */
    {
      id: "context", name: "Big picture & your archetype", tag: "Where you sit, and what kind of artist you actually are.",
      plain: "Before tactics, get honest about what winning means for YOU. Answer these 8 questions, then find your archetype. It changes what you should double down on.",
      blocks: [
        { type:"qa", id:"diagnostic", title:"The 8-question diagnostic", help:"No wrong answers. Write what's true, not what sounds good.", items:[
          {id:"d1", q:"When you imagine your career in 3 years, what does a good week look like?"},
          {id:"d2", q:"Would you still make music if no one listened?"},
          {id:"d3", q:"What do people most ask you for? (Performances / lessons / content / other)"},
          {id:"d4", q:"What have you actually been paid for in the last 12 months?"},
          {id:"d5", q:"Where do you spend creative time that does not feel like work?"},
          {id:"d6", q:"Do you care how many strangers know your name? (Deeply / Somewhat / Not really)"},
          {id:"d7", q:"Is your instinct to release music or to use it (sync, brand, education)?"},
          {id:"d8", q:"What would you stop doing tomorrow if money was not a factor?"}
        ]},
        { type:"chips", id:"archetype", title:"Based on the diagnostic, my primary archetype is:", single:true,
          options:[
            {v:"commercial", label:"Commercial Artist", desc:"You want reach, releases, a live career, streams."},
            {v:"noncommercial", label:"Non-Commercial Artist", desc:"You want your work used: sync, catalogue, teaching, grants."},
            {v:"creator", label:"Creator-Artist", desc:"Your audience and content are the engine."},
            {v:"mixed", label:"Mixed", desc:"A blend, and that's fine."}
          ]},
        { type:"info", title:"What to double down on, by archetype", body:[
          "Commercial Artist: Live circuit every month, 3–4 Reels/week, 6–8 singles/year, playlist pitching.",
          "Non-Commercial Artist: IPRS/PPL registration, sync catalogue, teaching roster, grant applications.",
          "Creator-Artist: Content consistency, platform SEO, brand media kit, engagement quality."
        ]},
        { type:"fill", id:"context_change", title:"", items:[
          {id:"change12", label:"The one thing I most want to change about my career in 12 weeks", ph:"One sentence", long:true}
        ]},
        { type:"checklist", id:"context_actions", title:"Your action items", items:[
          {id:"c_diag", text:"Complete the 8-question diagnostic above"},
          {id:"c_arch", text:"Identify your archetype and write what you'll double down on"},
          {id:"c_study", text:"Find 2 Indian indie artists 2 years ahead of you, study how they got there"},
          {id:"c_platforms", text:"List every platform where your music currently lives"}
        ]},
        { type:"note", id:"context_notes" }
      ]
    },

    /* 2 · IDENTITY -------------------------------------------------------- */
    {
      id: "identity", name: "Identity", tag: "What you stand for, who you're for, how it shows up everywhere.",
      plain: "This is the most important section. If you can say who you are in one sentence, every other decision gets easier.",
      blocks: [
        { type:"fill", id:"identity_sentence", title:"Write your identity sentence", help:"Fill in the blanks. Don't overthink the first pass.", items:[
          {id:"is_sound", label:"Your sound: I make ___ for ___.", ph:"e.g. moody Punjabi R&B for late-night drives"},
          {id:"is_ref", label:"Your sonic reference: My sound is ___ meets ___.", ph:"e.g. AP Dhillon meets Frank Ocean"},
          {id:"is_listener", label:"Your listener: My listener is ___ who feels ___.", ph:"e.g. a 19-year-old far from home who feels homesick"}
        ]},
        { type:"qa", id:"territory", title:"Your storytelling territory", help:"Where your realest songs come from. Take your time.", items:[
          {id:"t1", q:"What have you thought about most in the last 5 years that you've never fully explained to another person?"},
          {id:"t2", q:"What specific place, relationship, or period do you return to in unguarded moments?"},
          {id:"t3", q:"What do you understand about your language, city, community or generation that you don't hear other artists describing accurately?"}
        ]},
        { type:"fill", id:"identity_map", title:"Your identity map", help:"Pull the above together.", items:[
          {id:"im_sonic", label:"My sonic identity in one sentence", long:true},
          {id:"im_territory", label:"My storytelling territory (what I return to)", long:true},
          {id:"im_listener", label:"My specific listener (one person, one situation)", long:true},
          {id:"im_final", label:"The identity sentence, final version (under 15 words): I make ___ for ___.", ph:"Your finished sentence"}
        ]},
        { type:"table", id:"ladder", title:"Where are you on the credibility ladder?",
          help:"Tick the rung you're on now, then set your target for 12 weeks below.",
          columns:[
            {key:"rung", label:"Rung", type:"readonly"},
            {key:"desc", label:"What it looks like", type:"readonly"},
            {key:"here", label:"Here now?", type:"check"}
          ],
          rows:[
            {id:"r5", cells:{rung:"5 · Multi-city touring artist", desc:"3–5 city tour, 200–500 cap venues, festival billing, brand deals"}},
            {id:"r4", cells:{rung:"4 · Own headline show (50–150 cap)", desc:"Consistent releases, 10K+ monthly listeners, one press profile"}},
            {id:"r3", cells:{rung:"3 · Opening act / support slot", desc:"3+ releases, IPRS/PPL registered, 1K+ monthly listeners"}},
            {id:"r2", cells:{rung:"2 · Open mic / community shows", desc:"1–2 releases distributed, social presence, identity sentence written"}},
            {id:"r1", cells:{rung:"1 · Pre-release / production phase", desc:"No releases yet, identity forming, building skills"}}
          ]},
        { type:"chips", id:"ladder_now", title:"I am currently on rung:", single:true,
          options:[{v:"1",label:"1"},{v:"2",label:"2"},{v:"3",label:"3"},{v:"4",label:"4"},{v:"5",label:"5"}]},
        { type:"chips", id:"ladder_target", title:"My target rung in 12 weeks:", single:true,
          options:[{v:"1",label:"1"},{v:"2",label:"2"},{v:"3",label:"3"},{v:"4",label:"4"},{v:"5",label:"5"}]},
        { type:"checklist", id:"identity_actions", title:"Your action items", items:[
          {id:"i_blind", text:"Play 3 of your tracks back-to-back with no name visible. Ask a friend: are these the same artist?"},
          {id:"i_grid", text:"Screenshot your last 9 Instagram posts. Do they look like one artist? If not, that's your visual brief."},
          {id:"i_test", text:"Write your identity sentence and test it on someone outside music"},
          {id:"i_infl", text:"List your 3 biggest influences. For each: what sonic detail do you love? What's missing in all three?"},
          {id:"i_aud", text:"Define your audience in one sentence, a specific person in a specific situation, not 'music lovers in India'"}
        ]},
        { type:"note", id:"identity_notes" }
      ]
    },

    /* 3 · PRODUCTION ------------------------------------------------------ */
    {
      id: "production", name: "Production", tag: "A release workflow that matches your ambition.",
      plain: "Great songs stuck on your phone don't count. This is about finishing, and making the first 30 seconds impossible to skip.",
      blocks: [
        { type:"table", id:"anatomy", title:"Anatomy of your next song",
          help:"Streaming rewards songs that hook fast. Fill in your track's timestamps against the targets.",
          columns:[
            {key:"sec", label:"Section", type:"readonly"},
            {key:"target", label:"Target", type:"readonly"},
            {key:"yours", label:"Your track", type:"text"}
          ],
          rows:[
            {id:"intro", cells:{sec:"Intro", target:"Under 15 seconds"}},
            {id:"hook", cells:{sec:"First hook arrival", target:"Before 45 seconds"}},
            {id:"v1", cells:{sec:"Verse 1", target:"30–45 seconds"}},
            {id:"chorus", cells:{sec:"Chorus", target:"20–30 seconds"}},
            {id:"dur", cells:{sec:"Total duration", target:"Under 3:30"}}
          ]},
        { type:"qa", id:"sonic_test", title:"Sonic identity test", items:[
          {id:"st1", q:"What makes the first 5 seconds unmistakably you?"},
          {id:"st2", q:"What specific moment is the hook? (e.g. 'the line at 0:38')"},
          {id:"st3", q:"What will a listener feel at 1 minute? (name the emotion precisely)"}
        ]},
        { type:"table", id:"pipeline", title:"Your release pipeline",
          help:"Every track you have in flight. Where is it stuck?",
          columns:[
            {key:"name", label:"Track", type:"text"},
            {key:"stage", label:"Stage", type:"chips", options:["idea","demo","mixed","mastered","ready"]},
            {key:"block", label:"Blocking issue", type:"text"},
            {key:"window", label:"Release window", type:"text"}
          ], rows:6 },
        { type:"fill", id:"pipeline_q", title:"", items:[
          {id:"p_ready6", label:"How many releases do I have ready in the next 6 months?"},
          {id:"p_block", label:"What is blocking the tracks in early stages?", long:true}
        ]},
        { type:"checklist", id:"production_actions", title:"Your action items", items:[
          {id:"pr_30", text:"Run the 30-second test: play each track from 0:00. Would you skip it at 0:30 on a playlist? Fix the intro first."},
          {id:"pr_map", text:"Map your full release pipeline above"},
          {id:"pr_cadence", text:"Set a release cadence goal for the next 6 months"},
          {id:"pr_prod", text:"Research 2 producers in your genre you respect, reach out to one"},
          {id:"pr_cost", text:"Calculate the full cost of your last track (production, mix, master, art, distribution). Value for money?"}
        ]},
        { type:"note", id:"production_notes" }
      ]
    },

    /* 4 · DISTRIBUTION ---------------------------------------------------- */
    {
      id: "distribution", name: "Distribution", tag: "Everywhere it needs to be, with the right metadata.",
      plain: "Getting on Spotify is the easy part. Doing it with clean metadata, a real launch plan, and a plugged funnel is what separates you.",
      blocks: [
        { type:"table", id:"epk", title:"Your EPK (electronic press kit) checklist",
          help:"The pack you send to curators, press and venues. Mark each element.",
          columns:[
            {key:"el", label:"Element", type:"readonly"},
            {key:"status", label:"Status", type:"chips", options:["Done","In progress","Missing"]},
            {key:"link", label:"Link / notes", type:"text"}
          ],
          rows:[
            {id:"e1", cells:{el:"150-word bio, third person, identity sentence as the opening line"}},
            {id:"e2", cells:{el:"Best 3 tracks, embeddable streaming links"}},
            {id:"e3", cells:{el:"2 press photos (hi-res 300dpi+, consistent visual identity)"}},
            {id:"e4", cells:{el:"1–3 press quotes or reviews (or a notable curator quote)"}},
            {id:"e5", cells:{el:"Live performance video (even a phone video of a real show)"}},
            {id:"e6", cells:{el:"Contact + booking details with fee range"}}
          ]},
        { type:"fill", id:"epk_q", title:"", items:[
          {id:"epk_block", label:"Would you send this EPK to Wild City right now without editing? If no, what's the one thing blocking you?", long:true}
        ]},
        { type:"fill", id:"plan_release", title:"Plan your next release", items:[
          {id:"nr_title", label:"Track title"},
          {id:"nr_writers", label:"Composer / lyricist"},
          {id:"nr_date", label:"Target release date"},
          {id:"nr_distro", label:"Distributor"},
          {id:"nr_hook", label:"15–30 second hook moment (timestamp)"}
        ]},
        { type:"checklist", id:"prerelease", title:"Pre-release checklist", items:[
          {id:"x1", text:"Instrumental version ready"},
          {id:"x2", text:"ISRC code confirmed"},
          {id:"x3", text:"Composer / lyricist credits in distributor"},
          {id:"x4", text:"Language tag set correctly"},
          {id:"x5", text:"Mood and genre tags added"},
          {id:"x6", text:"Spotify editorial pitch submitted (at least 7 days before release)"},
          {id:"x7", text:"3 Reels / Shorts assets created from the 15–30 second hook"},
          {id:"x8", text:"YouTube video scheduled for release day"},
          {id:"x9", text:"Email list announcement drafted"},
          {id:"x10", text:"IPRS registration includes this composition"},
          {id:"x11", text:"Content ID confirmed active via distributor"}
        ]},
        { type:"table", id:"launch", title:"Your launch sequence",
          help:"The countdown. Tick each as you complete it.",
          columns:[
            {key:"when", label:"Timeline", type:"readonly"},
            {key:"do", label:"Action", type:"readonly"},
            {key:"done", label:"Done?", type:"check"}
          ],
          rows:[
            {id:"l6w", cells:{when:"6 weeks before", do:"Metadata complete. Distributor upload submitted. Instrumental uploaded."}},
            {id:"l4w", cells:{when:"4 weeks before", do:"3–5 Reels/Shorts created. Press note written. Email draft ready."}},
            {id:"l2w", cells:{when:"2 weeks before", do:"Press note sent to Rolling Stone India, Wild City, Indian Music Diaries. Pre-save link posted."}},
            {id:"l7d", cells:{when:"7 days before", do:"Spotify editorial pitch submitted. JioSaavn ArtistOne done. YouTube scheduled."}},
            {id:"l3d", cells:{when:"3 days before", do:"Pre-save Reel posted. Stories countdown begins. Email to list sent."}},
            {id:"lday", cells:{when:"Release day", do:"YouTube live. Release Reel posted. Stories with Spotify link. Reply to every comment."}},
            {id:"l25", cells:{when:"Days 2–5", do:"3 more Reels from different angles (BTS, lyric breakdown, process). Repost all UGC."}},
            {id:"lw2", cells:{when:"Week 2", do:"Check Spotify for Artists: saves, playlists, listener cities. Adjust spend to what's working."}}
          ]},
        { type:"table", id:"funnel", title:"Your fan funnel: where are you losing listeners?",
          help:"Fill in your real numbers. The leak is usually between 'heard it once' and 'came back'.",
          columns:[
            {key:"metric", label:"Metric", type:"readonly"},
            {key:"num", label:"Your number", type:"text"},
            {key:"bench", label:"Aim for", type:"readonly"}
          ],
          rows:[
            {id:"f1", cells:{metric:"Monthly Reel / Short views", bench:"-"}},
            {id:"f2", cells:{metric:"Monthly Spotify / JioSaavn streams", bench:"-"}},
            {id:"f3", cells:{metric:"Instagram followers", bench:"-"}},
            {id:"f4", cells:{metric:"Email list subscribers", bench:"5% of your follower count"}},
            {id:"f5", cells:{metric:"Paying fans (Patreon / merch / tickets)", bench:"1–5% of your email list"}}
          ]},
        { type:"checklist", id:"distribution_actions", title:"Your action items", items:[
          {id:"di_epk", text:"Complete the EPK checklist and identify the single missing element"},
          {id:"di_pre", text:"Complete the pre-release checklist for your next track"},
          {id:"di_compare", text:"Compare your distributor's terms with 2 alternatives"},
          {id:"di_meta", text:"Audit metadata on existing releases, are composer/lyricist credits correct on all?"},
          {id:"di_funnel", text:"Fill in your fan funnel numbers and find where you're losing listeners"}
        ]},
        { type:"note", id:"distribution_notes" }
      ]
    },

    /* 5 · RIGHTS ---------------------------------------------------------- */
    {
      id: "rights", name: "Rights", tag: "Own what you create. Collect what you're owed.",
      plain: "This is the boring section that quietly pays you for years. Every week you delay registering is money gone for good.",
      blocks: [
        { type:"checklist", id:"iprs", title:"IPRS · composition royalties (iprs.org)", items:[
          {id:"ip1", text:"Go to iprs.org and start the membership application"},
          {id:"ip2", text:"Gather documents: Aadhaar/passport, PAN, bank details, sample compositions"},
          {id:"ip3", text:"Pay one-time membership fee (~₹2,000–5,000)"},
          {id:"ip4", text:"Register each composition: title, co-writers + splits, ISRC, language"}
        ]},
        { type:"checklist", id:"ppl", title:"PPL · master rights (pplindia.org)", items:[
          {id:"pp1", text:"Register as a master rights owner at pplindia.org"},
          {id:"pp2", text:"Gather: recording metadata, UPC codes, release dates for all tracks"},
          {id:"pp3", text:"Confirm fee structure and submit"}
        ]},
        { type:"checklist", id:"contentid", title:"Distributor · Content ID", items:[
          {id:"ci1", text:"Log in to your distributor dashboard"},
          {id:"ci2", text:"Confirm Content ID is active for all released tracks"},
          {id:"ci3", text:"Confirm regional claiming is on (JioSaavn, Wynk, Gaana, YouTube Music)"}
        ]},
        { type:"table", id:"lawyer", title:"When you must get a music lawyer",
          help:"If any of these is live for you, don't sign before someone qualified reads it.",
          columns:[
            {key:"sit", label:"Situation", type:"readonly"},
            {key:"faced", label:"Facing this?", type:"chips", options:["Yes","No","Soon"]},
            {key:"notes", label:"Notes", type:"text"}
          ],
          rows:[
            {id:"lw1", cells:{sit:"Signing with any label, even 'indie-friendly'. Rights granted here are permanent."}},
            {id:"lw2", cells:{sit:"Any management agreement, check: 15–20% commission, no ownership of masters, exit clause"}},
            {id:"lw3", cells:{sit:"Any sync deal above ₹50,000, check: rights granted, territory, exclusivity period"}},
            {id:"lw4", cells:{sit:"Co-writer / co-producer split disputes. Sign a split sheet BEFORE release, not after."}}
          ]},
        { type:"table", id:"rights_audit", title:"Rights audit, your releases",
          columns:[
            {key:"track", label:"Track", type:"text"},
            {key:"iprs", label:"IPRS?", type:"chips", options:["Yes","No"]},
            {key:"ppl", label:"PPL?", type:"chips", options:["Yes","No"]},
            {key:"split", label:"Split sheet?", type:"chips", options:["Yes","No","n/a"]},
            {key:"master", label:"Who owns master?", type:"text"}
          ], rows:5 },
        { type:"fill", id:"rights_q", title:"", items:[
          {id:"r_unclaimed", label:"Rights I have not yet claimed", long:true},
          {id:"r_uncollected", label:"Estimated uncollected royalties"}
        ]},
        { type:"checklist", id:"rights_actions", title:"Your action items", items:[
          {id:"ra_iprs", text:"Register with IPRS if not done (iprs.org). Every week of delay is royalties lost."},
          {id:"ra_ppl", text:"Register with PPL India if not done (pplindia.org)"},
          {id:"ra_cid", text:"Confirm Content ID active on all released tracks"},
          {id:"ra_split", text:"Create a standard split-sheet template for future collabs (free at songsplit.com)"},
          {id:"ra_audit", text:"Complete the rights audit table for all existing releases"}
        ]},
        { type:"note", id:"rights_notes" }
      ]
    },

    /* 6 · REVENUE --------------------------------------------------------- */
    {
      id: "revenue", name: "Revenue", tag: "Multiple income streams that compound over time.",
      plain: "Streaming alone won't pay you. This maps the 7 ways artists actually earn, and which two you could switch on in 90 days.",
      blocks: [
        { type:"table", id:"rev_audit", title:"Revenue audit: which streams are you running?",
          columns:[
            {key:"stream", label:"Stream", type:"readonly"},
            {key:"status", label:"Status", type:"chips", options:["Active","Possible","Not yet"]},
            {key:"first", label:"First step to activate", type:"text"},
            {key:"target", label:"Monthly target ₹", type:"text"}
          ],
          rows:[
            {id:"rv1", cells:{stream:"01 · Live Performance"}},
            {id:"rv2", cells:{stream:"02 · Brand Partnerships"}},
            {id:"rv3", cells:{stream:"03 · YouTube"}},
            {id:"rv4", cells:{stream:"04 · Sync Licensing"}},
            {id:"rv5", cells:{stream:"05 · Direct Fan (Patreon / merch)"}},
            {id:"rv6", cells:{stream:"06 · Teaching / Workshops"}},
            {id:"rv7", cells:{stream:"07 · Beat Licensing / Session work"}}
          ]},
        { type:"table", id:"income_audit", title:"Income audit: what has actually paid",
          help:"Real numbers from the last 12 months. Log barter at market rate.",
          columns:[
            {key:"cat", label:"Category", type:"readonly"},
            {key:"measure", label:"What to measure", type:"readonly"},
            {key:"amt", label:"Last 12 months ₹", type:"text"},
            {key:"net", label:"Net after costs", type:"text"}
          ],
          rows:[
            {id:"in1", cells:{cat:"Live income", measure:"Gig fees, net of travel/equipment"}},
            {id:"in2", cells:{cat:"Streaming royalties", measure:"DSP + YouTube + PPL/IPRS payouts"}},
            {id:"in3", cells:{cat:"Brand / content", measure:"Paid brand deals + sponsored content"}},
            {id:"in4", cells:{cat:"Teaching / session", measure:"Lessons + session fees"}},
            {id:"in5", cells:{cat:"Other", measure:"Sync, merch, crowdfunding, grants"}},
            {id:"in6", cells:{cat:"TOTAL", measure:""}}
          ]},
        { type:"fill", id:"profit_first", title:"Profit-first goal setting", items:[
          {id:"pf1", label:"What is the minimum music must earn (net of costs) to keep you in the game?"},
          {id:"pf2", label:"What is your total annual cost base? (production, distribution, gear, travel, marketing)"},
          {id:"pf3", label:"Which income stream gives the best return per hour of effort?"},
          {id:"pf4", label:"If you need ₹___ / year and currently earn ₹___, the gap is ₹___. What closes it?", long:true}
        ]},
        { type:"checklist", id:"revenue_actions", title:"Your action items", items:[
          {id:"re_audit", text:"Complete the revenue audit, mark each of the 7 streams Active / Possible / Not yet"},
          {id:"re_calc", text:"Calculate your total music income for the last 12 months"},
          {id:"re_two", text:"Identify 2 streams you earn zero from now but could activate in 90 days"},
          {id:"re_brand", text:"Research 1 brand whose audience overlaps yours, find their marketing lead on LinkedIn"},
          {id:"re_target", text:"Set a 6-month revenue target, broken down by stream"}
        ]},
        { type:"note", id:"revenue_notes" }
      ]
    },

    /* 7 · SOCIAL ---------------------------------------------------------- */
    {
      id: "social", name: "Social media", tag: "Platforms as distribution, not performance.",
      plain: "You're not 'posting content'. You're choosing how your music spreads. Figure out which engine you're underusing.",
      blocks: [
        { type:"table", id:"spread", title:"How music actually spreads",
          help:"Six ways songs travel. Which are you actually using?",
          columns:[
            {key:"mech", label:"Mechanism", type:"readonly"},
            {key:"using", label:"Using it?", type:"chips", options:["Yes","A bit","No"]},
            {key:"now", label:"What you do now", type:"text"},
            {key:"change", label:"One change", type:"text"}
          ],
          rows:[
            {id:"m1", cells:{mech:"Algorithm push (Spotify / YouTube recommendation)"}},
            {id:"m2", cells:{mech:"Editorial placement (playlist, press feature)"}},
            {id:"m3", cells:{mech:"Social virality (Reel audio trend, meme)"}},
            {id:"m4", cells:{mech:"Peer recommendation (word of mouth, WhatsApp)"}},
            {id:"m5", cells:{mech:"Media coverage (Wild City, Rolling Stone India)"}},
            {id:"m6", cells:{mech:"Live conversion (show attendee → fan)"}}
          ]},
        { type:"fill", id:"spread_q", title:"", items:[
          {id:"underinvested", label:"Which mechanism am I most underinvested in?"}
        ]},
        { type:"table", id:"content_audit", title:"Content audit: your last 20 posts",
          columns:[
            {key:"post", label:"Post", type:"readonly"},
            {key:"desc", label:"Describe it + platform", type:"text"},
            {key:"why", label:"Why it worked / flopped", type:"text"}
          ],
          rows:[
            {id:"ca1", cells:{post:"Top post 1"}},
            {id:"ca2", cells:{post:"Top post 2"}},
            {id:"ca3", cells:{post:"Top post 3"}},
            {id:"ca4", cells:{post:"Lowest post 1"}},
            {id:"ca5", cells:{post:"Lowest post 2"}},
            {id:"ca6", cells:{post:"Lowest post 3"}}
          ]},
        { type:"fill", id:"content_q", title:"", items:[
          {id:"top_common", label:"What do my top posts have in common?", long:true},
          {id:"low_common", label:"What do my lowest posts have in common?", long:true}
        ]},
        { type:"table", id:"community", title:"5 community actions this week",
          columns:[
            {key:"act", label:"Action", type:"readonly"},
            {key:"done", label:"Done?", type:"check"},
            {key:"notes", label:"Notes", type:"text"}
          ],
          rows:[
            {id:"cm1", cells:{act:"Attend one open mic in your city, even if not performing. Watch, meet, connect."}},
            {id:"cm2", cells:{act:"Share another artist's post with genuine commentary (a comment that shows you listened)"}},
            {id:"cm3", cells:{act:"Identify 5 artists at your stage. Reach out to one, not to ask for anything, to start a peer relationship."}},
            {id:"cm4", cells:{act:"Propose one collab with an artist whose audience overlaps yours but doesn't know you yet"}},
            {id:"cm5", cells:{act:"Start a mailing list, even 10 subscribers. Email bypasses algorithmic gatekeeping."}}
          ]},
        { type:"checklist", id:"social_actions", title:"Your action items", items:[
          {id:"so_mech", text:"Complete the mechanics table, find your most underused mechanism"},
          {id:"so_audit", text:"Audit your last 20 posts, note which content gets saved vs just liked"},
          {id:"so_one", text:"Choose 1 platform to go deeper on this month"},
          {id:"so_cal", text:"Build a 4-week content calendar: 3 post types, specific days and times"},
          {id:"so_email", text:"Start your email list today (Mailchimp or ConvertKit free tier)"}
        ]},
        { type:"note", id:"social_notes" }
      ]
    },

    /* 8 · LIVE & NETWORKING ---------------------------------------------- */
    {
      id: "live", name: "Live & networking", tag: "Perform strategically. Build relationships that compound.",
      plain: "One good show and one real relationship can move your career more than 50 posts. Plan both deliberately.",
      blocks: [
        { type:"fill", id:"live_review", title:"Your live strategy: last 12 months", items:[
          {id:"lv_shows", label:"Total live shows played"},
          {id:"lv_fee", label:"Average fee per show (₹)"},
          {id:"lv_income", label:"Total live income this year (₹)"},
          {id:"lv_open", label:"Which shows opened new opportunities, and why?", long:true},
          {id:"lv_impact", label:"Which show had the most career impact so far, and why?", long:true}
        ]},
        { type:"table", id:"live_plan", title:"Next 6 months: your live plan",
          columns:[
            {key:"venue", label:"Venue / festival", type:"text"},
            {key:"type", label:"Type", type:"chips", options:["open mic","support","headline","festival"]},
            {key:"date", label:"Target date", type:"text"},
            {key:"angle", label:"Your pitch angle", type:"text"}
          ], rows:3 },
        { type:"table", id:"collab", title:"Before you collaborate: what to agree",
          help:"Agree these BEFORE you start, not after the song is done.",
          columns:[
            {key:"item", label:"Item to agree", type:"readonly"},
            {key:"status", label:"Status for your next collab", type:"text"}
          ],
          rows:[
            {id:"co1", cells:{item:"Credits, how it's billed ('ft.' vs '×' vs co-production)"}},
            {id:"co2", cells:{item:"Royalty split, default 50/50, adjust for real contribution. Use songsplit.com."}},
            {id:"co3", cells:{item:"Promo commitment, both post, both tag, agreed platforms and date"}},
            {id:"co4", cells:{item:"Who owns the master, usually producer / lead artist unless agreed"}},
            {id:"co5", cells:{item:"Release timeline, agree a date range before you start"}}
          ]},
        { type:"table", id:"followup", title:"Networking follow-up system",
          help:"The follow-up is where the value is. Log every meaningful contact.",
          columns:[
            {key:"name", label:"Contact", type:"text"},
            {key:"ctx", label:"Where/how you met", type:"text"},
            {key:"date", label:"Date", type:"text"},
            {key:"sent", label:"Follow-up sent?", type:"chips", options:["Yes","No"]},
            {key:"next", label:"Next step", type:"text"}
          ], rows:5 },
        { type:"checklist", id:"live_actions", title:"Your action items", items:[
          {id:"li_venues", text:"List 10 venues in your city you haven't played but should, research their booking contact"},
          {id:"li_fests", text:"Research 3 festivals with open submissions in your genre, note their windows"},
          {id:"li_collab", text:"Reach out to 1 artist for a co-bill or collab (be specific in your ask)"},
          {id:"li_log", text:"Start logging every meaningful contact in the table above"},
          {id:"li_48", text:"Follow up within 48 hours on any industry conversation, reference the actual conversation"}
        ]},
        { type:"note", id:"live_notes" }
      ]
    },

    /* 9 · SCALE & TEAM ---------------------------------------------------- */
    {
      id: "team", name: "Scale & team", tag: "Infrastructure to grow beyond what you can do alone.",
      plain: "You can't do everything forever. Map who's on your team, who's missing, and what you can hand off first.",
      blocks: [
        { type:"table", id:"team_state", title:"Your team: current state",
          columns:[
            {key:"role", label:"Role", type:"readonly"},
            {key:"person", label:"Person (or vacant)", type:"text"},
            {key:"does", label:"What they do for you", type:"text"},
            {key:"ok", label:"Working?", type:"chips", options:["Yes","No","n/a"]},
            {key:"gap", label:"Gap?", type:"text"}
          ],
          rows:[
            {id:"tm1", cells:{role:"Manager"}},
            {id:"tm2", cells:{role:"Booking agent"}},
            {id:"tm3", cells:{role:"PR / press contact"}},
            {id:"tm4", cells:{role:"Social media"}},
            {id:"tm5", cells:{role:"Mixing engineer"}},
            {id:"tm6", cells:{role:"Mastering engineer"}},
            {id:"tm7", cells:{role:"Collaborating artists"}},
            {id:"tm8", cells:{role:"Sound engineer (live)"}},
            {id:"tm9", cells:{role:"Label / distributor contact"}}
          ]},
        { type:"info", title:"Where to find each team member", body:[
          "Session musicians: live shows, referrals from artists you respect; AirGigs / SoundBetter for remote. Do one session before committing.",
          "Mixing engineer: find mixes you love, credit-search on Spotify for Artists; Lost Stories Academy alumni. Send a test track before paying for the full project.",
          "Collaborating artists: shows, Instagram DMs, open-mic scenes, who appears alongside you on playlists. Listen to 3+ of their songs, have a coffee first.",
          "Manager: they usually find you, be visible and professional with a clear trajectory. Check their roster: are you a priority or a portfolio filler?"
        ]},
        { type:"fill", id:"team_q", title:"", items:[
          {id:"tq_deleg", label:"The task that takes most of my time but could be delegated", long:true},
          {id:"tq_need", label:"What my career most needs right now (management / PR / booking / label)"},
          {id:"tq_before", label:"What I need in place before approaching a manager", long:true}
        ]},
        { type:"checklist", id:"team_actions", title:"Your action items", items:[
          {id:"te_deck", text:"Write a one-page artist deck (bio, best tracks, live history, metrics) for industry conversations"},
          {id:"te_mgr", text:"Identify 3 managers who work with artists at your stage, research their rosters"},
          {id:"te_admin", text:"List every weekly admin task, circle the one that drains the most music-making time"},
          {id:"te_system", text:"Set up 1 system that saves you 2+ hours/week (scheduling tool, template emails, asset folder)"}
        ]},
        { type:"note", id:"team_notes" }
      ]
    },

    /* 10 · ADVANCED REVENUE & POSITIONING -------------------------------- */
    {
      id: "advanced", name: "Advanced revenue & positioning", tag: "Sync, a contact pipeline, long-term career architecture.",
      plain: "This is how careers stop being random. Turn your contacts into a pipeline you work 15 minutes a day.",
      blocks: [
        { type:"table", id:"contact_audit", title:"Contact audit: your network by category",
          help:"Sort real people into these buckets. Warm contacts convert 5–10x better than cold.",
          columns:[
            {key:"cat", label:"Category", type:"readonly"},
            {key:"who", label:"Who belongs here (names)", type:"text"},
            {key:"ask", label:"What you can ask them for", type:"readonly"},
            {key:"when", label:"When to activate", type:"readonly"}
          ],
          rows:[
            {id:"na1", cells:{cat:"Warm advocates, have hired/booked/recommended you", ask:"Re-hire, referral, testimonial", when:"First, they already trust you"}},
            {id:"na2", cells:{cat:"Warm potentials, know your work, never hired you", ask:"An intro chat, not a pitch, ask what they're working on", when:"Second, reactivate before cold"}},
            {id:"na3", cells:{cat:"Referral nodes, connectors with wide networks", ask:"A specific intro, not 'keep me in mind'", when:"When you have something specific to pitch"}},
            {id:"na4", cells:{cat:"Cold targets, brands/venues/press you've never met", ask:"A compelling cold approach with social proof", when:"Last"}},
            {id:"na5", cells:{cat:"Latent contacts, silent 12+ months, remember you", ask:"A genuine reconnect, 'how's your project?' first", when:"Ongoing"}}
          ]},
        { type:"table", id:"pipeline_active", title:"Your current pipeline: active conversations",
          columns:[
            {key:"opp", label:"Contact / opportunity", type:"text"},
            {key:"stage", label:"Stage", type:"chips", options:["early","mid","close"]},
            {key:"needed", label:"What's needed to move forward", type:"text"},
            {key:"next", label:"Next action", type:"text"}
          ], rows:5 },
        { type:"table", id:"weekly_pipeline", title:"Weekly pipeline actions (15 min/day)",
          columns:[
            {key:"day", label:"Day", type:"readonly"},
            {key:"act", label:"Action", type:"readonly"},
            {key:"done", label:"Done this week?", type:"check"}
          ],
          rows:[
            {id:"wp1", cells:{day:"Monday", act:"Follow up on outstanding proposals or unanswered pitches from last week"}},
            {id:"wp2", cells:{day:"Wednesday", act:"One warm outreach, reactivate a latent contact or check in with a warm potential"}},
            {id:"wp3", cells:{day:"Friday", act:"One new cold pitch, or one new connection (show, DM, LinkedIn)"}},
            {id:"wp4", cells:{day:"End of month", act:"Income audit + pipeline review: what closed? what stalled? what needs a new approach?"}}
          ]},
        { type:"fill", id:"adv_q", title:"", items:[
          {id:"adv_stage", label:"My goal: move from Transactional → Pipeline → Architectural revenue. Current stage:"}
        ]},
        { type:"checklist", id:"advanced_actions", title:"Your action items", items:[
          {id:"ad_audit", text:"Run the 10-minute contact audit: phone contacts + Instagram + email, sort into the 5 categories"},
          {id:"ad_warm", text:"Identify your 3 warmest advocates, reach out to one this week with a specific ask"},
          {id:"ad_inst", text:"Create instrumentals of your 5 most commercially viable tracks (for sync)"},
          {id:"ad_sync", text:"Research 3 sync licensing platforms or agents operating in India"},
          {id:"ad_5yr", text:"Map your 5-year milestones in concrete terms: releases, revenue, team"}
        ]},
        { type:"note", id:"advanced_notes" }
      ]
    },

    /* 11 · 90-DAY PLAN ---------------------------------------------------- */
    {
      id: "plan", name: "Your 90-day plan", tag: "What you've built, and exactly what comes next.",
      plain: "This is the payoff. A concrete 3-month plan with verifiable milestones. Tick these off in real life over the next 90 days.",
      blocks: [
        { type:"checklist", id:"m1_identity", title:"Month 1 · Foundation · Weeks 1–2: Identity", items:[
          {id:"m1a", text:"Complete the identity sentence, share with 3 people outside music for feedback"},
          {id:"m1b", text:"Answer the 3 territory questions, a paragraph each"},
          {id:"m1c", text:"Audit your last 9 Instagram posts, do they look like one artist?"},
          {id:"m1d", text:"Listen to 3 tracks back-to-back, sonic identity test"},
          {id:"m1e", text:"Define your specific listener in one sentence"},
          {id:"m1f", text:"Write a new bio using the identity sentence as the opening line"}
        ]},
        { type:"checklist", id:"m1_setup", title:"Month 1 · Weeks 3–4: Production setup + Rights", items:[
          {id:"m1g", text:"Audit your setup, which tier are you at? What's missing?"},
          {id:"m1h", text:"Buy one missing Tier 1 item if under ₹15,000"},
          {id:"m1i", text:"Record one demo in your treated space, compare to untreated"},
          {id:"m1j", text:"Message 3 mixing engineers on SoundBetter, get quotes"},
          {id:"m1k", text:"iprs.org, start membership and gather documents"},
          {id:"m1l", text:"pplindia.org, start master rights registration"},
          {id:"m1m", text:"Distributor dashboard, confirm Content ID active"},
          {id:"m1n", text:"Verify composer/lyricist credits on all existing releases"}
        ]},
        { type:"checklist", id:"m2", title:"Month 2 · Build · Release, distribution, social", items:[
          {id:"m2a", text:"Choose your distributor, DistroKid or Madverse for most emerging artists"},
          {id:"m2b", text:"Set up distributor with correct royalty recipient details"},
          {id:"m2c", text:"Plan your next release, a single, 4–6 weeks from today"},
          {id:"m2d", text:"Complete pre-release metadata checklist for the single"},
          {id:"m2e", text:"Submit Spotify editorial pitch 7+ days before release"},
          {id:"m2f", text:"Create 3–5 Reels/Shorts from the track's 15–30s hook"},
          {id:"m2g", text:"Write the press note, send to Rolling Stone India, Wild City, Indian Music Diaries"},
          {id:"m2h", text:"Milestone: 1 track submitted to Spotify editorial (confirmation email received)"},
          {id:"m2i", text:"Milestone: distributor confirmed and active (login + payment saved)"},
          {id:"m2j", text:"Milestone: 4-week content calendar created (dates, topics, platform)"},
          {id:"m2k", text:"Milestone: email list exists (even 0 subscribers, infrastructure in place)"},
          {id:"m2l", text:"Milestone: IPRS application submitted (reference number received)"}
        ]},
        { type:"checklist", id:"m3", title:"Month 3 · Revenue · First income streams", items:[
          {id:"m3a", text:"Research 10 venues in your city that book indie artists"},
          {id:"m3b", text:"Build an artist pitch pack: EPK with bio, photos, links, 2–3 demos"},
          {id:"m3c", text:"Send 5 booking enquiries this month"},
          {id:"m3d", text:"Apply to 2 college cultural committee mailing lists for fest season"},
          {id:"m3e", text:"Build a media kit: 1 page with audience demographics, engagement rate, rate card"},
          {id:"m3f", text:"Identify 3 brands whose audience overlaps yours, follow their marketing leads on LinkedIn"},
          {id:"m3g", text:"Offer 1 product-for-content collaboration to a brand in your niche"},
          {id:"m3h", text:"Post one 'available for lessons' Story, test demand"},
          {id:"m3i", text:"Target: 1 live booking, even unpaid (prove you can deliver a set)"},
          {id:"m3j", text:"Target: 1 brand email sent to a real decision-maker with your media kit"},
          {id:"m3k", text:"Target: 50 email subscribers"},
          {id:"m3l", text:"Target: 1 release live with correct metadata, Content ID active, IPRS confirmed"}
        ]},
        { type:"pillars", id:"review", title:"Baseline vs now: where you've moved", mode:"review",
          help:"Re-rate each pillar. Seeing the movement is the whole point." },
        { type:"fill", id:"plan_close", title:"", items:[
          {id:"focus90", label:"My single most important focus for the next 90 days", long:true},
          {id:"partner90", label:"My accountability partner for the next 90 days (a friend, another artist, anyone who'll check on you)"}
        ]},
        { type:"checklist", id:"plan_actions", title:"Your action items", items:[
          {id:"pl_work", text:"Work through the 3-month checklists above, mark what's already done"},
          {id:"pl_partner", text:"Choose 1 accountability partner and schedule a 90-day check-in"},
          {id:"pl_share", text:"Share your 90-day plan with someone who'll hold you to it"},
          {id:"pl_reread", text:"Re-read your identity sentence, has it changed?"}
        ]},
        { type:"note", id:"plan_notes" }
      ]
    },

    /* 12 · RESOURCES ------------------------------------------------------ */
    {
      id: "resources", name: "Resources", tag: "The tools and contacts you'll keep coming back to.",
      plain: "Bookmark this. Fill in your own account links as you set each one up.",
      blocks: [
        { type:"table", id:"tools", title:"Key platforms and tools",
          columns:[
            {key:"tool", label:"Platform / tool", type:"readonly"},
            {key:"purpose", label:"Purpose", type:"readonly"},
            {key:"link", label:"Your account / link", type:"text"}
          ],
          rows:[
            {id:"to1", cells:{tool:"IPRS · iprs.org", purpose:"Register compositions, collect performance royalties"}},
            {id:"to2", cells:{tool:"PPL India · pplindia.org", purpose:"Register masters, collect neighbouring rights"}},
            {id:"to3", cells:{tool:"DistroKid / Madverse", purpose:"Distribution to all DSPs"}},
            {id:"to4", cells:{tool:"Spotify for Artists", purpose:"Pitch to editorial, view analytics"}},
            {id:"to5", cells:{tool:"JioSaavn ArtistOne", purpose:"Pitch to JioSaavn editorial"}},
            {id:"to6", cells:{tool:"Mailchimp / ConvertKit", purpose:"Email list, your owned audience"}},
            {id:"to7", cells:{tool:"songsplit.com", purpose:"Free split-sheet template for collaborations"}},
            {id:"to8", cells:{tool:"SoundBetter / AirGigs", purpose:"Find remote session musicians and engineers"}},
            {id:"to9", cells:{tool:"India Indie Music Radar", purpose:"indiemusicindia.com/reviewers, 900+ curator database"}}
          ]},
        { type:"table", id:"press", title:"Media and press contacts",
          columns:[
            {key:"pub", label:"Publication", type:"readonly"},
            {key:"link", label:"Submission link / email", type:"text"},
            {key:"resp", label:"Response time", type:"text"},
            {key:"last", label:"Last submitted", type:"text"}
          ],
          rows:[
            {id:"pr1", cells:{pub:"Rolling Stone India"}},
            {id:"pr2", cells:{pub:"Wild City"}},
            {id:"pr3", cells:{pub:"Indian Music Diaries"}},
            {id:"pr4", cells:{pub:"Homegrown"}}
          ]},
        { type:"table", id:"industry_contacts", title:"Industry contacts you make",
          columns:[
            {key:"name", label:"Name", type:"text"},
            {key:"role", label:"Role / company", type:"text"},
            {key:"met", label:"How you met", type:"text"},
            {key:"contact", label:"Email / contact", type:"text"},
            {key:"status", label:"Follow-up", type:"text"}
          ], rows:6 },
        { type:"checklist", id:"resources_actions", title:"Your action items", items:[
          {id:"rs_links", text:"Fill in your current account links for each platform above"},
          {id:"rs_radar", text:"Use indiemusicindia.com/reviewers to find 10 free press curators to pitch"},
          {id:"rs_log", text:"Log every industry contact you make in the table above"}
        ]},
        { type:"note", id:"resources_notes" }
      ]
    }
  ]
};
