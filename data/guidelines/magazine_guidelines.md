---
title: "Fedora Magazine — Writing Guidelines"
source: https://docs.fedoraproject.org/en-US/fedora-magazine/writing-guidelines/
last_updated: 2026-05-14
---

# Tips for article style, grammar, content, and SEO

These tips will help your article sail through editing. Be kind to your editor(s),
and read this before you start.

---

## Markup

Primary rule: don't get too fancy. Legibility is important.

1. **Don't mix monospace fonts with proportional fonts in a sentence.** Use italics
   for the special text. For instance, don't write `dnf install foo` in the middle
   of a sentence, write *dnf install foo*.

2. **Use italics for system objects you mention in a sentence:**
   - GUI or CLI elements like button text or menu entries
   - other prompts the reader must find on the screen
   - commands or package names

3. **Use the Preformatted style in the WP Engine editor for command line input or
   output.** Use a shell prompt (`$` or `#`) only where it genuinely affects the
   meaning, or to set the input apart from output. It also helps to use boldface
   for the input itself:

       $ command arg1 arg2
       output line 1
       output line 2

4. **Use boldface only for an extremely important phrase or statement.**

---

## Grammar and style tips

1. **Use sentence case for the post title and heading titles.** Don't capitalize
   words in your article title or any heading, other than proper nouns. This avoids
   needless arguments about title case, which differs by region.
   - Incorrect heading: *Use Sentence Case for Post Titles in Fedora Magazine*
   - Correct heading: *Use sentence case for post titles in Fedora Magazine*

2. **Check spelling and grammar.** Nobody likes nitpicky comments about this. Check
   your work before you send it to an editor. Editors: double-check all the work,
   that's your job!

3. **Write clearly and use shorter sentences.** Brevity is good. Clarity is better.
   Don't be excessively wordy when avoidable. If a longer sentence is easier to
   read, use the extra words.

4. **Avoid passive voice.** Passive voice is the use of the object of a sentence as
   the subject. For example:
   - *Active voice*: The troops defeated the enemy.
   - *Passive voice*: The enemy was defeated by the troops.

5. **Be careful of gerunds (-ing words).** They usually indicate passive voice.
   Rewrite your sentence to make it stronger. For example:
   - *Weak, passive voice*: Setting the foobar configuration option will make the
     application listen on all interfaces.
   - *Strong, active voice*: Set the foobar configuration option to make the
     application listen on all interfaces.

6. **Avoid unnecessary future tense.** Unless you're actually talking about future
   plans or publications, present tense is best.
   - *Unnecessary future tense*: When you select **Run**, your program will start.
   - *Present tense*: When you select **Run**, your program starts.

7. **Avoid too much use of the verb *to be* in sentences.** Too much use of *is*,
   *will be*, or *can be* makes your sentences weak and flabby.
   - *Weak*: Zambone is an app used for managing your private documents on a server.
   - *Strong*: Zambone manages your private documents on a server. Or: Use Zambone
     to manage your private documents on a server.
   - *Weak*: When setting up a file server, it is important to plan the directory
     structure carefully.
   - *Strong*: Plan the directory structure of the file server carefully before you
     set it up.

8. **Use standard US English for spelling and other international differences.**
   US English is the lingua franca for the Fedora Project overall.

9. **Have a smooth flow from general information to specific instructions.** If
   you're not sure how to structure your article, check out the starter template.

---

## Content tips

These tips are about things to do — and avoid — in what you tell users to do.
Remember that thousands of readers trust Fedora Magazine to tell them how to carry
out tasks. Be responsible and helpful, advocate best practices, and respect the
user's security and choice.

1. **Leave packaged files alone.** Processes should not involve editing files under
   system folders like */usr* or */lib*. Edit */etc* or a user-specific
   configuration in the home directory.

2. **Prefer free software where practical (and officially packaged software wherever
   possible).** The Magazine can still cover non-FOSS software where we know it is
   very popular and useful to Fedora users (Google Chrome is a good example). But if
   your article covers a general process, use FOSS software.

3. **Use libvirt/KVM in tips, not VirtualBox or other hypervisors.** The KVM
   hypervisor and libvirt in Fedora are FOSS and part of the platform.

4. **Unless necessary, use Fedora family distributions.** Use installations,
   containers, or distributions within the Fedora family (Fedora, CentOS, RHEL)
   unless the point of your article is to explain a cross-distribution mechanism.

5. **Copr software must be accompanied by a caveat.** The Copr build system is not
   managed by the Fedora release team and does not provide official software builds.
   Include a statement like: *Copr is not officially supported by Fedora
   infrastructure. Use packages at your own risk.*

6. **Avoid exclusionary or problematic language.**
   - **blacklist/whitelist** — Use *allowlist/denylist* instead.
   - **master/slave** — Use *primary/secondary*, *primary/replica*,
     *active/passive*, or *active/standby*.

7. **Test your process.** If possible, use a fresh guest VM — or at least a
   brand-new user account. Run your process from beginning to end to ensure it
   works. Fix, rinse, and repeat.

8. **Use the correct style for third parties.** A non-exhaustive list:
   - **Copr** instead of *COPR*
   - **NVIDIA** instead of *Nvidia* or *nVidia*
   - **Perl** instead of *PERL*
   - **Red Hat** instead of *Redhat* or *RedHat*
   - **ThinkPad** instead of *Thinkpad*

---

## Image and screenshot tips

1. **Use a fresh, standard Fedora Workstation**, not your personal desktop or setup.
   It's best to make a VM with a fresh Fedora Workstation install and do the steps
   there.

2. **Set screen resolution at a reasonable but not too high resolution**, such as
   1280x960 or 1280x800.

3. If you're only showing a browser window, make it fairly large on the screen and
   **screenshot only the browser**.

4. If you're only showing an application, **use the default size of the app to
   screenshot it**.

5. **Upload and use that original media in your article.** If the shot is large,
   choose a medium size thumbnail and let WP Engine handle the conversion.

---

## WP Engine tips

1. **Use a simple, relevant title.** Preferably a call to action like *Build a
   widget using GTK+*, or a list description like *5 fun games in Fedora*. The
   title affects search engines and drives traffic to the Magazine.

2. **Provide a featured image.** See the
   [featured image guide](https://fedoramagazine.org/creating-a-featured-image-for-a-fedora-magazine-article/)
   for tips. You can also ask the editors to assign this for you. If you make your
   own image, match the style of other images and use the provided assets. Don't add
   your own fonts or deviate from the guide.

3. **Use good SEO practices.** Use the SEO plugin to maximize the search ranking of
   the article. Aim for a "green" rating in the *Publish* box at the top right of
   your article's edit screen.
   - Enter a meaningful keyword in the SEO box under your article. Most articles
     shouldn't use *Fedora* as their keyword.
   - If the Snippet doesn't give an effective introduction or summary, rewrite it.
   - Don't feel like you have to eliminate every warning. A "green" rating overall
     is the only goal.

4. **Use the Edit as HTML option when pasting into preformatted blocks.** Current
   versions of WP Engine are known to strip leading hash marks (`#`) and leading
   whitespace when content is pasted into preformatted blocks. Use the *Edit as
   HTML* option prior to pasting, paste your content between the `<pre>` tags, then
   switch back to *Edit visually*.

---

## Other hints

Got an idea for better writing? Discuss with the editors in the
[#magazine:fedoraproject.org](https://matrix.to/#/#magazine:fedoraproject.org?web-instance%5Belement.io%5D=chat.fedoraproject.org)
Matrix channel on chat.fedoraproject.org.

---

*Source: https://docs.fedoraproject.org/en-US/fedora-magazine/writing-guidelines/
— Last content update: 2026-05-14*