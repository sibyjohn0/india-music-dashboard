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
      lesson:{ idea:"You can't fix what you won't measure. Start by telling the truth about where you are.", points:["This isn't a test. A low score just shows you where the biggest wins are hiding.","The artists who grow fastest are honest on day one, not the ones who look good on paper.","You'll re-rate these at the end. Watching the numbers move is the reward."] },
      blocks: [
        { type:"info", title:"How to use this workbook", body:[
          "Work through one section at a time. You don't have to finish it in one sitting, everything saves as you go.",
          "Fill things in as you decide them, not 'later'. A rough answer you can improve beats a blank you never return to.",
          "The action items in each section are the minimum you commit to before moving on.",
          "Come back and change earlier answers as you grow. Your identity, your plan, your numbers, all of it will shift. That's the point."
        ]},
        { type:"fill", id:"you", title:"First, what do we call you?", items:[{id:"name", label:"Your name or artist name", ph:"e.g. Rohit"}] },
        { type:"chips", id:"artist_lang", single:true, title:"What language do you mostly make music in?", help:"This tunes the videos, artists and news we show you across the workbook.", options:[{v:"Punjabi",label:"Punjabi"},{v:"Hindi",label:"Hindi"},{v:"English",label:"English"},{v:"Tamil",label:"Tamil"},{v:"Telugu",label:"Telugu"},{v:"Malayalam",label:"Malayalam"},{v:"Kannada",label:"Kannada"},{v:"Bengali",label:"Bengali"},{v:"Marathi",label:"Marathi"},{v:"Instrumental",label:"Instrumental / no words"},{v:"Other",label:"Other"}] },
        { type:"chips", id:"artist_city", single:true, title:"Which city are you closest to?", help:"So we can point you to the right venues, shows and local scene.", options:[{v:"mumbai",label:"Mumbai"},{v:"delhi",label:"Delhi"},{v:"bengaluru",label:"Bengaluru"},{v:"hyderabad",label:"Hyderabad"},{v:"pune",label:"Pune"},{v:"goa",label:"Goa"},{v:"other",label:"Somewhere else"}] },
        { type:"pillars", id:"baseline", title:"Your baseline self-assessment",
          help:"Rate yourself 1–10 on each pillar, then note your biggest strength and biggest gap. This is your 'before' picture. You'll compare against it at the end.",
          gloss:"Quick translations: Distribution = getting your songs onto Spotify and Apple. Rights = registering so you actually get paid. Revenue diversity = more than one way money comes in. Infrastructure = the people and tools around you. New to all this? Rate low and move on, that's the point." },
        { type:"fill", id:"baseline_top", title:"Sum it up", items:[
          {id:"strengths3", label:"My top 3 strengths right now", ph:"e.g. melodies, consistency, my live energy", long:true},
          {id:"gaps3", label:"My top 3 gaps right now", ph:"e.g. distribution, no press, no email list", long:true},
          {id:"goal1", label:"My single most important goal for this programme", ph:"One clear goal", long:true}
        ]},
        { type:"checklist", id:"start_actions", title:"Your action items", items:[
          {id:"a_baseline", text:"Complete the baseline self-assessment above"},
          {id:"a_bio", text:"Write a 2-sentence artist bio you can share anywhere"},
          {id:"a_goals", text:"Set 3 goals for the next 12 weeks and write them down"},
          {id:"a_intro", text:"Share your bio in one community or group you're part of"},
          {id:"a_handles", text:"Grab the same @handle everywhere you can (Instagram, YouTube, Spotify, JioSaavn) and your name, before someone else takes it"}
        ]},
        { type:"note", id:"start_notes" }
      ]
    },

    /* 1 · CONTEXT & DIAGNOSTIC -------------------------------------------- */
    {
      id: "context", name: "Big picture & your archetype", tag: "Where you sit, and what kind of artist you actually are.",
      plain: "Before tactics, get honest about what winning means for you. Answer these 8 questions, then find your archetype. It changes what you should double down on.",
      lesson:{ idea:"'Making it' means different things for different artists. Copying the wrong role model is the most common way to waste years.", points:["There are broadly four kinds of artist: Commercial (reach and releases), Non-Commercial (sync, teaching, catalogue), Creator-Artist (audience and content), and Mixed.","Your archetype decides what you double down on. A Creator-Artist chasing playlists, or a Commercial artist ignoring live, both stall.","Study 2 Indian artists 2 years ahead of you in YOUR lane, not the biggest names in a different one."] },
      deepen:{ compare:true, watch:true, news:true },
      blocks: [
        { type:"qa", id:"diagnostic", title:"The 8-question diagnostic", help:"No wrong answers. Write what's true, not what sounds good.",
          gloss:"If a word is new: 'sync' means your music used in a film, ad or show. 'Brand' means paid work with a company. Just answer in your own words.", items:[
          {id:"d1", q:"When you imagine your career in 3 years, what does a good week look like?"},
          {id:"d2", q:"Would you still make music if no one listened?"},
          {id:"d3", q:"What do people most ask you for? (Performances / lessons / content / other)"},
          {id:"d4", q:"What have you actually been paid for in the last 12 months?", ph:"e.g. one wedding gig, or nothing yet, both are fine"},
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
          "Creator-Artist: content consistency, getting found in search on YouTube and Spotify, a brand media kit, and quality engagement.",
          "In plain words: playlist pitching = asking curators to add your song. Sync catalogue = songs ready for films and ads to license. Media kit = a one-page pack about you. Don't stress about all of these now, just note the two that fit you."
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
      lesson:{ idea:"If you can't say who you are in one sentence, no algorithm, curator or fan can either.", points:["Your identity sentence is simple: I make ___ for ___. Specific beats broad. Music for everyone reaches no one.","Your strongest songs come from your territory: the places, people and years you keep returning to. Mine that, don't borrow someone else's.","The test: 3 songs back to back, 9 posts in a grid. Do they feel like one artist? Consistency is what makes you recognisable.","Know your rung on the credibility ladder. You climb it one clear step at a time, not in one jump."] },
      deepen:{ compare:true },
      blocks: [
        { type:"fill", id:"identity_sentence", title:"Write your identity sentence", help:"Fill in the blanks. Don't overthink the first pass.", items:[
          {id:"is_sound", label:"Your sound: I make ___ for ___.", ph:"e.g. moody Punjabi R&B for late-night drives"},
          {id:"is_ref", label:"Your sonic reference: My sound is ___ meets ___.", ph:"e.g. AP Dhillon meets Frank Ocean"},
          {id:"is_listener", label:"Your listener: My listener is ___ who feels ___.", ph:"e.g. a 19-year-old far from home who feels homesick"}
        ]},
        { type:"qa", id:"territory", title:"Your storytelling territory", help:"Where your realest songs come from. Take your time.", items:[
          {id:"t1", q:"What have you thought about most in the last 5 years that you've never fully explained to another person?", ph:"e.g. leaving my town, a friendship that ended, faith, money at home"},
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
          gloss:"Quick words: support / opening act = you play before the main artist. Headline = the show is under your name. Cap = how many people the venue holds. Monthly listeners = the number on your Spotify profile. Not sure? Pick the lowest rung that sounds like you.",
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
      lesson:{ idea:"On streaming, the first 30 seconds decide everything. A great song no one finishes doesn't count.", points:["Hook before 0:45, keep it under 3:30. Play every track from 0:00 and ask: would I skip this at 0:30 on a playlist?","The first 5 seconds should be unmistakably you. Name the exact moment that is your hook.","Finished and out beats perfect and stuck. Set a release cadence, say one song every 6 weeks, and protect it.","Know the full cost of a track (production, mix, master, art, distribution) so you can tell what's worth it."] },
      deepen:{ watch:true, read:[{label:"New-release checklist",href:"/toolkit/new-release-checklist/"}] },
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
          {id:"pr_cadence", text:"Set how often you'll release, for example one song every 6 weeks"},
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
      lesson:{ idea:"Getting on Spotify is easy. Getting found, and keeping the listeners you get, is the real game.", points:["A distributor puts you everywhere; clean metadata (credits, language, tags, ISRC) is what makes you discoverable and paid.","Your EPK is the one pack that opens doors with curators, venues and press. Build it once, keep it sharp.","A release is a sequence, not a day. Work the launch plan from 6 weeks out so pitching windows aren't missed.","Watch your fan funnel: the leak is usually between heard-it-once and came-back. An email list or WhatsApp Channel is how you own the relationship."] },
      deepen:{ read:[{label:"Build your EPK (guide)",href:"/guides/electronic-press-kit-epk-india/"},{label:"12-week release plan",href:"/guides/12-week-release-plan-india/"},{label:"Get on Spotify editorial playlists",href:"/guides/spotify-editorial-playlists-india/"},{label:"Playlist target sheet",href:"/toolkit/streaming-playlist-target-sheet-india/"}] },
      blocks: [
        { type:"table", id:"epk", tools:[{kind:"template",label:"EPK / one-sheet template",href:"/toolkit/one-sheet-example/"},{kind:"template",label:"Label copy template",href:"/toolkit/label-copy-template/"}], title:"Your EPK (electronic press kit) checklist",
          help:"The pack you send to curators, press and venues. Mark each element.",
          gloss:"An EPK is just a one-page pack about you: a short bio, your best songs, 2 photos, a live video, and how to reach you. That's it. Only have rough tracks, mp3s and no logo yet? Totally normal, build these pieces one at a time.",
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
        { type:"fill", id:"plan_release", tools:[{kind:"template",label:"Release plan example",href:"/toolkit/release-plan-example/"}], title:"Plan your next release", gloss:"A few words you'll see a lot: DSP = a streaming app (Spotify, Apple, JioSaavn, Amazon). Pre-save = a link fans tap before release day so the song auto-saves when it drops. Editorial = a real person at a streaming app choosing to playlist you. UGC = posts fans make that you can re-share.", items:[
          {id:"nr_title", label:"Track title"},
          {id:"nr_writers", label:"Composer / lyricist"},
          {id:"nr_date", label:"Target release date"},
          {id:"nr_distro", label:"Distributor"},
          {id:"nr_hook", label:"15–30 second hook moment (timestamp)"}
        ]},
        { type:"checklist", id:"prerelease", tools:[{kind:"template",label:"New release checklist",href:"/toolkit/new-release-checklist/"},{kind:"template",label:"Song metadata sheet",href:"/toolkit/song-master-metadata-sheet/"},{kind:"template",label:"Playlist target sheet",href:"/toolkit/streaming-playlist-target-sheet-india/"}], title:"Pre-release checklist",
          gloss:"Quick words: ISRC is a free ID code your distributor gives each song. Metadata is the song's info: title, credits, language, genre. Content ID is what claims your song on YouTube so you get paid for it.", items:[
          {id:"x1", text:"Instrumental version ready"},
          {id:"x2", text:"ISRC code confirmed"},
          {id:"x3", text:"Composer / lyricist credits in distributor"},
          {id:"x4", text:"Language tag set correctly"},
          {id:"x5", text:"Mood and genre tags added"},
          {id:"x6", text:"Spotify editorial pitch submitted (at least 7 days before release)"},
          {id:"x7", text:"3 Reels / Shorts / Moj assets created from the 15–30 second hook"},
          {id:"x8", text:"YouTube video scheduled for release day"},
          {id:"x9", text:"Email list announcement drafted"},
          {id:"x10", text:"IPRS registration includes this composition"},
          {id:"x11", text:"Content ID confirmed active via distributor"}
        ]},
        { type:"table", id:"launch", tools:[{kind:"template",label:"Social media calendar",href:"/toolkit/social-media-calendar/"}], title:"Your launch sequence",
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
            {id:"l7d", cells:{when:"7 days before", do:"Spotify editorial pitch submitted. JioSaavn ArtistOne done. Amazon Music for Artists pitch submitted. YouTube scheduled."}},
            {id:"l3d", cells:{when:"3 days before", do:"Pre-save Reel posted. Stories countdown begins. Email to list sent."}},
            {id:"lday", cells:{when:"Release day", do:"YouTube live. Release Reel posted. Stories with Spotify link. Reply to every comment."}},
            {id:"l25", cells:{when:"Days 2–5", do:"3 more Reels from different angles (BTS, lyric breakdown, process). Repost all UGC."}},
            {id:"lw2", cells:{when:"Week 2", do:"Check Spotify for Artists: saves, playlists, listener cities. Adjust spend to what's working."}}
          ]},
        { type:"table", id:"funnel", tools:[{kind:"template",label:"Email sign-up sheet",href:"/toolkit/email-sign-up-sheet/"}], title:"Your fan funnel: where are you losing listeners?",
          help:"Fill in your real numbers. The leak is usually between 'heard it once' and 'came back'.",
          gloss:"Brand new? Most of these will be zero or blank, and that's completely normal. Put a real number where you have one, and treat the blanks as your first targets.",
          columns:[
            {key:"metric", label:"Metric", type:"readonly"},
            {key:"num", label:"Your number", type:"text"},
            {key:"bench", label:"Aim for", type:"readonly"}
          ],
          rows:[
            {id:"f1", cells:{metric:"Monthly Reel / Short views", bench:"-"}},
            {id:"f2", cells:{metric:"Monthly Spotify / JioSaavn / Amazon streams", bench:"-"}},
            {id:"f3", cells:{metric:"Instagram followers", bench:"-"}},
            {id:"f4", cells:{metric:"Email list subscribers", bench:"5% of your follower count"}},
            {id:"f5", cells:{metric:"Paying fans (Patreon / merch / tickets)", bench:"1–5% of your email list"}}
          ]},
        { type:"checklist", id:"distribution_actions", title:"Your action items", items:[
          {id:"di_epk", text:"Complete the EPK checklist and identify the single missing element"},
          {id:"di_pre", text:"Complete the pre-release checklist for your next track"},
          {id:"di_compare", text:"Compare your distributor's terms (DistroKid/Madverse) with 2 others: e.g. Believe, TuneCore or RouteNote. Check the cut, payout speed and India support."},
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
      lesson:{ idea:"The boring paperwork is where artists quietly lose, or keep, real money for years.", points:["IPRS pays you for the composition, PPL for the recording. Register early: every month you wait is royalties gone for good.","Content ID claims your song across YouTube and regional apps so you get paid when it's used.","Sign a split sheet BEFORE a collab is released, never after. A 10-minute job that prevents the ugliest fights.","Know the moments you must not sign without a music lawyer: any label deal, any management contract, any big sync."] },
      deepen:{ read:[{label:"IPRS & PPL registration guide",href:"/toolkit/iprs-ppl-registration-guide/"},{label:"Register your copyright (IPRS)",href:"/guides/register-music-copyright-iprs-india/"},{label:"Co-writer split sheet",href:"/toolkit/co-writer-split-sheet/"}] },
      blocks: [
        { type:"checklist", id:"iprs", tools:[{kind:"guide",label:"IPRS & PPL registration guide",href:"/toolkit/iprs-ppl-registration-guide/"},{kind:"guide",label:"ISRC & UPC code guide",href:"/toolkit/isrc-upc-code-guide/"}], title:"IPRS · composition royalties (iprs.org)",
          gloss:"IPRS pays you when your song is performed or played in public. PPL (next) pays you for the actual recording. Both are one-time to join and then pay you for years. Do it even if it feels too early.", items:[
          {id:"ip1", text:"Go to iprs.org and start the membership application"},
          {id:"ip2", text:"Gather documents: Aadhaar/passport, PAN, bank details, sample compositions"},
          {id:"ip3", text:"Pay the one-time join fee (~₹1,200 as an author or composer, ₹2,200 as a publisher)"},
          {id:"ip4", text:"Register each composition: title, co-writers + splits, ISRC, language"}
        ]},
        { type:"checklist", id:"ppl", title:"PPL · master rights (pplindia.org)", gloss:"UPC is a barcode-style ID for a whole release (a single or EP); your distributor generates it for you.", items:[
          {id:"pp1", text:"Register as a master rights owner at pplindia.org"},
          {id:"pp2", text:"Gather: recording metadata, UPC codes, release dates for all tracks"},
          {id:"pp3", text:"Confirm fee structure and submit"}
        ]},
        { type:"checklist", id:"contentid", title:"Distributor · Content ID", items:[
          {id:"ci1", text:"Log in to your distributor dashboard"},
          {id:"ci2", text:"Confirm Content ID is active for all released tracks"},
          {id:"ci3", text:"Confirm regional claiming is on (JioSaavn, Amazon Music, YouTube Music)"}
        ]},
        { type:"table", id:"lawyer", tools:[{kind:"contract",label:"Producer agreement",href:"/toolkit/producer-agreement-india/"},{kind:"contract",label:"Artist management agreement",href:"/toolkit/artist-management-agreement/"},{kind:"contract",label:"Sync licensing agreement",href:"/toolkit/sync-licensing-agreement-india/"},{kind:"contract",label:"Publishing admin agreement",href:"/toolkit/publishing-admin-agreement-india/"}], title:"When you must get a music lawyer",
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
        { type:"table", id:"rights_audit", tools:[{kind:"contract",label:"Co-writer split sheet",href:"/toolkit/co-writer-split-sheet/"}], title:"Rights audit, your releases",
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
        { type:"builder", id:"remix_deal", title:"Draft a simple remix or sample agreement", file:"remix-sample-agreement",
          help:"Answer a few taps and you get a plain, ready-to-send agreement you can copy or save. This is for a remix or someone sampling your song. A cover, a paid feature, or any label deal needs its own agreement and a lawyer.",
          fields:[
            {id:"orig", kind:"text", label:"Your artist name (the original artist)", ph:"Your name"},
            {id:"other", kind:"text", label:"The other person's name", ph:"Their name"},
            {id:"track", kind:"text", label:"Which track is this about?", ph:"Track title"},
            {id:"use", kind:"chips", label:"What are they making?", options:["A remix","A sample of my song"]},
            {id:"platforms", kind:"chips", label:"Where are they allowed to post it?", options:["Instagram only","Instagram and YouTube","All streaming platforms","Anywhere"]},
            {id:"monet", kind:"chips", label:"Can it be monetised?", options:["No, not on any platform","Yes, and we split earnings","Yes, they keep the earnings"]},
            {id:"split", kind:"chips", label:"If it earns money, my share is", options:["50%","60%","70%","80%","100%"], showIf:{f:"monet", is:["Yes, and we split earnings"]}},
            {id:"credit", kind:"chips", label:"How am I credited?", options:["Full credit to me on every post","Co-credit, both names","Producer-style credit"]},
            {id:"revoke", kind:"chips", label:"Can I pull it down later?", options:["Yes, with 14 days notice","No, permanent once posted"]}
          ],
          template:[
            "REMIX / SAMPLE AGREEMENT",
            "",
            "Between {orig} (the original artist) and {other}.",
            "Track: {track}",
            "What is being made: {use}",
            "",
            "Where it can be posted: {platforms}.",
            "Monetisation: {monet}.",
            {when:{f:"monet", is:["Yes, and we split earnings"]}, text:"If it earns money, {orig} receives {split} of net earnings."},
            "Credit: {credit}.",
            "Ownership: {orig} owns the original song. This permission covers the use described above only and transfers no rights in the original.",
            "Ending it: {revoke}.",
            "",
            "Both people agree to the above.",
            "",
            "{orig}: ______________   Date: ________",
            "{other}: ______________   Date: ________",
            "",
            "This is a plain-language starting point, not legal advice. It assumes {orig} owns or controls the original song and does not clear anyone else's rights. For any paid, exclusive, or label deal, get a music lawyer."
          ] },
        { type:"checklist", id:"rights_actions", title:"Your action items", items:[
          {id:"ra_iprs", text:"Register with IPRS if not done (iprs.org). Every week of delay is royalties lost."},
          {id:"ra_ppl", text:"Register with PPL India if not done (pplindia.org)"},
          {id:"ra_cid", text:"Confirm Content ID active on all released tracks"},
          {id:"ra_split", text:"Create a standard split-sheet template for future collabs (free at songsplits.com)"},
          {id:"ra_audit", text:"Complete the rights audit table for all existing releases"}
        ]},
        { type:"note", id:"rights_notes" }
      ]
    },

    /* 6 · REVENUE --------------------------------------------------------- */
    {
      id: "revenue", name: "Revenue", tag: "Multiple income streams that compound over time.",
      plain: "Streaming alone won't pay you. This maps the 7 ways artists actually earn, and which two you could switch on in 90 days.",
      lesson:{ idea:"Streaming alone won't pay your rent. Careers are built on several income streams that compound.", points:["There are 7 realistic streams: live, brand, YouTube, sync, direct-fan, teaching, and beat or session work.","Profit-first: know the minimum music must earn you and your yearly cost base, then close the gap on purpose.","You don't need all 7. Pick the 2 you earn nothing from today but could switch on in 90 days.","Measure return per hour, not just rupees. The stream that pays best for your effort is where to lean."] },
      deepen:{ read:[{label:"Royalty calculator",href:"/tools/royalty-calculator/"},{label:"How Spotify royalties work in India",href:"/guides/how-spotify-royalties-work-india/"},{label:"Revenue streams checklist",href:"/toolkit/revenue-streams-checklist/"},{label:"Sync licensing in India",href:"/guides/sync-licensing-music-ads-film-india/"}] },
      blocks: [
        { type:"table", id:"rev_audit", tools:[{kind:"template",label:"Revenue streams checklist",href:"/toolkit/revenue-streams-checklist/"},{kind:"template",label:"Artist finances template",href:"/toolkit/artist-finances-template/"}], title:"Revenue audit: which streams are you running?",
          gloss:"Two that trip people up: 'Sync licensing' = your song placed in a film, ad, show or game. 'Direct fan' = money straight from fans, like Patreon, merch or tickets.",
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
        { type:"table", id:"income_audit", tools:[{kind:"tool",label:"Royalty calculator",href:"/tools/royalty-calculator/"},{kind:"template",label:"Annual profit & loss template",href:"/toolkit/annual-profit-loss-template/"}], title:"Income audit: what has actually paid",
          help:"Real numbers from the last 12 months. Log barter at market rate.",
          gloss:"Haven't earned from music yet? Write 0 and move on. This is your starting line, not a score.",
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
      lesson:{ idea:"Treat platforms as distribution, not performance. You're not posting for applause, you're choosing how your music travels.", points:["Music spreads six ways: algorithm, editorial, social trends, peer word-of-mouth, media, and live conversion. Find the one you're most underusing.","Saves and shares matter more than likes. Study which posts got saved, and make more of those.","In India, don't default to Instagram-only. ShareChat, Moj, Josh and WhatsApp Channels carry real regional-language reach.","Community beats broadcast: genuine comments, peer relationships and a mailing list outlast any single viral moment."] },
      deepen:{ watch:true, read:[{label:"Pitch music blogs & press",href:"/guides/pitch-music-blogs-press-india/"}] },
      blocks: [
        { type:"table", id:"spread", title:"How music actually spreads",
          help:"Six ways songs travel. Which are you actually using?",
          gloss:"'Algorithm push' = Spotify or YouTube recommending you automatically. 'Editorial' = a real human putting you on a playlist or writing about you. 'Peer' = one person sending your song to another.",
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
          gloss:"Don't have 20 posts yet? Fill in whatever you've got, even 2 or 3, and leave the rest.",
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
        { type:"table", id:"community", tools:[{kind:"template",label:"Social media calendar",href:"/toolkit/social-media-calendar/"},{kind:"template",label:"Marketing routine checklist",href:"/toolkit/marketing-routine-checklist/"}], title:"5 community actions this week",
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
            {id:"cm5", cells:{act:"Start a mailing list or a WhatsApp Channel, even 10 subscribers. Email and WhatsApp reach fans directly, past the algorithm."}}
          ]},
        { type:"checklist", id:"social_actions", title:"Your action items", items:[
          {id:"so_mech", text:"Complete the mechanics table, find your most underused mechanism"},
          {id:"so_audit", text:"Audit your last 20 posts, note which content gets saved vs just liked"},
          {id:"so_one", text:"Choose 1 platform to go deeper on this month"},
          {id:"so_cal", text:"Build a 4-week content calendar: 3 post types, specific days and times, across Instagram Reels, YouTube Shorts and one India-first app (ShareChat/Moj, Josh or WhatsApp Channels) if it fits your language"},
          {id:"so_email", text:"Start your email list today (Mailchimp or ConvertKit free tier)"}
        ]},
        { type:"note", id:"social_notes" }
      ]
    },

    /* 8 · LIVE & NETWORKING ---------------------------------------------- */
    {
      id: "live", name: "Live & networking", tag: "Perform strategically. Build relationships that compound.",
      plain: "One good show and one real relationship can move your career more than 50 posts. Plan both deliberately.",
      lesson:{ idea:"One great show and one real relationship can move your career more than fifty posts.", points:["Play strategically. Which past show actually opened doors, and why? Do more of that, not just any gig.","Relationships compound: follow up within 48 hours, referencing the real conversation, or the moment is wasted.","Before any collaboration, agree credits, splits, promo and who owns the master. In writing, up front.","Warm rooms convert: give a live audience one clear next step, follow, save, or join the mailing list."] },
      deepen:{ cityLinks:true, compare:true, read:[{label:"Upcoming shows & festivals",href:"/live/"},{label:"Book live gigs (guide)",href:"/guides/book-live-gigs-independent-band-india/"},{label:"Show-booking email template",href:"/toolkit/show-booking-email-template/"}] },
      blocks: [
        { type:"fill", id:"live_review", title:"Your live strategy: last 12 months", gloss:"No shows yet? Put 0 and skip to the plan below. Everyone starts at zero.", items:[
          {id:"lv_shows", label:"Total live shows played"},
          {id:"lv_fee", label:"Average fee per show (₹)"},
          {id:"lv_income", label:"Total live income this year (₹)"},
          {id:"lv_open", label:"Which shows opened new opportunities, and why?", long:true},
          {id:"lv_impact", label:"Which show had the most career impact so far, and why?", long:true}
        ]},
        { type:"table", id:"live_plan", tools:[{kind:"venues",label:"Browse venues in your city",href:"/venues/{city}/"},{kind:"outreach",label:"Show-booking email template",href:"/toolkit/show-booking-email-template/"},{kind:"template",label:"Booking advance sheet",href:"/toolkit/booking-advance-sheet/"}], title:"Next 6 months: your live plan",
          columns:[
            {key:"venue", label:"Venue / festival", type:"text"},
            {key:"type", label:"Type", type:"chips", options:["open mic","support","headline","festival"]},
            {key:"date", label:"Target date", type:"text"},
            {key:"angle", label:"Your pitch angle", type:"text"}
          ], rows:3 },
        { type:"table", id:"collab", tools:[{kind:"contract",label:"Co-writer split sheet",href:"/toolkit/co-writer-split-sheet/"},{kind:"contract",label:"Producer agreement",href:"/toolkit/producer-agreement-india/"}], title:"Before you collaborate: what to agree",
          help:"Agree these BEFORE you start, not after the song is done.",
          columns:[
            {key:"item", label:"Item to agree", type:"readonly"},
            {key:"status", label:"Status for your next collab", type:"text"}
          ],
          rows:[
            {id:"co1", cells:{item:"Credits, how it's billed ('ft.' vs '×' vs co-production)"}},
            {id:"co2", cells:{item:"Royalty split, default 50/50, adjust for real contribution. Use songsplits.com."}},
            {id:"co3", cells:{item:"Promo commitment, both post, both tag, agreed platforms and date"}},
            {id:"co4", cells:{item:"Who owns the master, usually producer / lead artist unless agreed"}},
            {id:"co5", cells:{item:"Release timeline, agree a date range before you start"}}
          ]},
        { type:"table", id:"followup", tools:[{kind:"template",label:"Contact directory template",href:"/toolkit/contact-directory-template/"}], title:"Networking follow-up system",
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
      lesson:{ idea:"You can't do everything forever. Growth comes from building the infrastructure to do less of the wrong work.", points:["Map your team and the gaps. The first hire is usually whatever admin task steals the most music-making time.","Know where each person is found: engineers via credits and test tracks, collaborators via shows and DMs, managers usually find you when you're visible and consistent.","With a manager, check: are you a priority artist on their roster, or portfolio filler?","One system that saves you 2+ hours a week (templates, a scheduler, an asset folder) buys back creative time."] },
      deepen:{ read:[{label:"Media 101",href:"/toolkit/media-101-guide-india/"},{label:"Working with publicists",href:"/toolkit/publicists-101-guide-india/"}] },
      blocks: [
        { type:"table", id:"team_state", tools:[{kind:"contract",label:"Artist management agreement",href:"/toolkit/artist-management-agreement/"},{kind:"template",label:"Personnel / team doc",href:"/toolkit/personnel-doc/"}], title:"Your team: current state",
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
      id: "advanced", name: "Advanced revenue & positioning", tag: "Sync, a contact pipeline, and a career that lasts.",
      plain: "This is how careers stop being random. Turn your contacts into a pipeline you work 15 minutes a day.",
      lesson:{ idea:"Careers stop being random when your contacts become a pipeline you work a little every day.", points:["Sort your network into warm advocates, warm potentials, referral nodes, cold targets and latent contacts. Warm converts 5 to 10 times better than cold.","Work it 15 minutes a day: follow up Monday, one warm reach Wednesday, one new pitch Friday.","Move from Transactional (chasing one-off gigs) to Pipeline (a steady flow) to Architectural (income that keeps coming).","Build a sync catalogue: instrumental versions of your most placeable songs, ready when an opportunity lands."] },
      deepen:{ read:[{label:"Sync licensing in India",href:"/guides/sync-licensing-music-ads-film-india/"}] },
      blocks: [
        { type:"table", id:"contact_audit", tools:[{kind:"template",label:"Contact directory template",href:"/toolkit/contact-directory-template/"},{kind:"template",label:"Competition analysis template",href:"/toolkit/competition-analysis-template/"}], title:"Contact audit: your network by category",
          help:"Sort real people into these buckets. Warm contacts convert 5–10x better than cold.",
          gloss:"'Warm' = people who already know you. 'Cold' = people you've never met. Always start with warm, they're far more likely to say yes.",
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
          gloss:"The 'Transactional to Pipeline to Architectural' line below means: Transactional = chasing one-off gigs. Pipeline = a steady flow of conversations on the go. Architectural = income that keeps coming without chasing each one.",
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
      lesson:{ idea:"A plan you can't verify is just a wish. This turns everything above into 90 days of concrete moves.", points:["Month 1 is foundation: identity, recording setup and rights. Month 2 is build: release, distribution, social. Month 3 is revenue: first income streams.","Every milestone is checkable: a confirmation email, a booking, 50 subscribers, not a vibe.","Pick one accountability partner and a single most-important focus. Focus beats a long to-do list.","Re-rate your 8 pillars against week one. Seeing the movement is the proof it worked."] },
      deepen:{ read:[{label:"12-week release plan",href:"/guides/12-week-release-plan-india/"}], news:true },
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
          {id:"m1g", text:"Audit your recording setup: mic, interface, headphones, room. List what's missing."},
          {id:"m1h", text:"Buy one missing basic if it's under ₹15,000 (a mic, interface or headphones)"},
          {id:"m1i", text:"Record one demo, then hang a blanket or duvet behind you to soften echo and record again. Hear the difference."},
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
      lesson:{ idea:"Keep this shelf close. The tools and contacts here are the ones you'll come back to for years.", points:["Fill in your own account links as you set each one up, so your whole setup lives in one place.","Our reviewer list, venue pages, radar and royalty calculator do a lot of the legwork for free.","Log every industry contact you make. Future-you will thank present-you."] },
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
            {id:"to5b", cells:{tool:"Amazon Music for Artists", purpose:"Pitch to Amazon editorial, claim your profile"}},
            {id:"to5c", cells:{tool:"YouTube for Artists / Studio", purpose:"Claim your official artist channel, see analytics"}},
            {id:"to6", cells:{tool:"Mailchimp / ConvertKit", purpose:"Email list, your owned audience"}},
            {id:"to7", cells:{tool:"songsplits.com", purpose:"Free split-sheet template for collaborations"}},
            {id:"to8", cells:{tool:"SoundBetter / AirGigs", purpose:"Find remote session musicians and engineers"}},
            {id:"to9", cells:{tool:"India Indie Music Radar", purpose:"[900+ curators & reviewers](/reviewers/) and [the artist radar](/radar.html)"}},
            {id:"to10", cells:{tool:"Venues & live shows", purpose:"[Venues by city](/venues/) and [upcoming shows](/live/)"}},
            {id:"to11", cells:{tool:"The toolkit & royalty calculator", purpose:"[Guides & templates](/toolkit/) and the [royalty calculator](/tools/royalty-calculator/)"}}
          ]},
        { type:"table", id:"press", title:"Media and press contacts",
          help:"Tip: our [reviewer list](/reviewers/) already has 900+ curators with submission info.",
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
          {id:"rs_radar", text:"Use the [reviewer list](/reviewers/) to find 10 free press curators to pitch"},
          {id:"rs_log", text:"Log every industry contact you make in the table above"}
        ]},
        { type:"note", id:"resources_notes" }
      ]
    }
  ]
};
