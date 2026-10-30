<p align="center">
  <img src="./envy-banner-animated.svg" width="100%" alt="ENVY — a different frequency, in neon pink and cyan" />
</p>

<p align="center">
  <b>LOCAL AI &nbsp; / &nbsp; LINUX &nbsp; / &nbsp; RECOVERY &nbsp; / &nbsp; PRIVACY</b>
</p>

<p align="center">
  <a href="#-featured-envy-terminal">Terminal AI</a> &nbsp; · &nbsp;
  <a href="#-the-black-veil-workshop">BLACK VEIL</a> &nbsp; · &nbsp;
  <a href="#-find-me-elsewhere">Find me</a>
</p>

<p align="center">
  I'm <b>Envy</b> — a curious mind building tools with a little neon and a lot of intention.<br />
  Local intelligence, systems worth exploring, and a way back when something breaks.<br /><br />
  <i>A little shell magic. I still eat glitter. ✨</i>
</p>

---

## ✦ Featured: ENVY Terminal

<a href="https://github.com/xzchick/envy-terminal"><img src="https://raw.githubusercontent.com/xzchick/envy-terminal/main/docs/assets/hero.svg" width="100%" alt="ENVY Terminal — local AI, your documents, and evidence you can inspect" /></a>

**My AI workspace, entirely in Terminal.** Fast local answers, a deeper Fable mode, searchable documents, and research with sources you can inspect.

<table>
  <tr>
    <td width="33%" valign="top"><b>⌘ THINK LOCALLY</b><p>Switch between quick everyday chat and detailed work. Models run on your Mac.</p><code>/fast</code> &nbsp; <code>/deep</code></td>
    <td width="33%" valign="top"><b>▧ FOLLOW THE EVIDENCE</b><p>Search PDFs, read scanned pages with local OCR, and distinguish facts from allegations.</p><code>/library-find</code> &nbsp; <code>/check</code></td>
    <td width="33%" valign="top"><b>◇ KEEP CONTROL</b><p>Save chats deliberately, choose what to remember, and turn web research off.</p><code>/chat-save</code> &nbsp; <code>/offline</code></td>
  </tr>
</table>

<p align="center">
  <a href="https://github.com/xzchick/envy-terminal"><b>Explore ENVY Terminal →</b></a> &nbsp; · &nbsp;
  <a href="https://github.com/xzchick/envy-terminal/blob/main/docs/SETUP.md">Install it</a> &nbsp; · &nbsp;
  <a href="https://github.com/xzchick/envy-terminal/blob/main/docs/COMMANDS.md">Command guide</a>
</p>

<details>
<summary><b>See it in Terminal</b></summary>
<br />
<img src="https://raw.githubusercontent.com/xzchick/envy-terminal/main/docs/assets/terminal-demo.png" width="100%" alt="ENVY Terminal indexing and searching a fictional local document" />

<sub>Illustrative terminal render using a fictional fixture and real indexing output. No personal documents or account information are shown.</sub>
</details>

<sub>macOS-first · Python · Ollama · SQLite · Vision OCR · Local inference has no provider token bill. Online research still contacts external sources; model answers require verification.</sub>

## ✧ The BLACK VEIL workshop

A Linux environment and a growing set of tools for system visibility, recovery, and deliberate control.

<table>
  <tr>
    <td width="50%" valign="top">
      <a href="https://github.com/xzchick/envy-black-veil"><img src="./profile-assets/envy-black-veil.svg" width="100%" alt="ENVY BLACK VEIL — Linux desktop and system tools" /></a>
      <p><b>A desktop with its own identity.</b> AlmaLinux + KDE Plasma, searchable utilities, live command output, and a cohesive dark interface.</p>
      <p><code>AlmaLinux</code> <code>KDE Plasma</code> <code>Python</code> <code>RPM</code></p>
      <sub>Development candidate · Installer and desktop testing in progress.</sub>
    </td>
    <td width="50%" valign="top">
      <a href="https://github.com/xzchick/envy-black-veil"><img src="./profile-assets/envy-reclaim.svg" width="100%" alt="RECLAIM — recovery, one block at a time" /></a>
      <p><b>Make recovery visible.</b> A 1,024-block recovery map driven by GNU ddrescue progress for disk-image recovery.</p>
      <p><code>Python</code> <code>Qt</code> <code>GNU ddrescue</code></p>
      <sub>In development · Part of the BLACK VEIL toolset.</sub>
    </td>
  </tr>
</table>

<p align="center"><a href="https://github.com/xzchick/envy-black-veil"><b>Explore BLACK VEIL →</b></a></p>

<details>
<summary><b>Inside the workshop — development screenshots</b></summary>
<br />

[![RECLAIM recovery-map development preview](./reclaim-development.png)](./reclaim-development.png)

<sub>Synthetic recovery-map test data; not a real disk recovery result.</sub>

<table><tr>
<td width="50%" valign="top"><b>COMMAND CENTER</b><br /><br /><img src="./command-center-development.png" width="100%" alt="Command Center development interface" /><p>Searchable launchers, system actions, and an output panel.</p><sub>Idle development interface; no action running.</sub></td>
<td width="50%" valign="top"><b>OPS DESK</b><br /><br /><img src="./ops-desk-development.png" width="100%" alt="Ops Desk development interface using a sample task" /><p>Encrypted local planning, role aliases, progress, and check-ins.</p><sub>Development preview using test data.</sub></td>
</tr></table>
</details>

<details>
<summary><b>Explore the BLACK VEIL toolset</b></summary>

## ⌘ Inside BLACK VEIL

<p>Purpose-built tools sharing one dark, neon interface. These are part of my development suite; Linux desktop and workflow testing is ongoing.</p>

<table>
  <tr>
    <td width="50%" valign="top"><b>◈ GUARDIAN · Know your system</b><p>SELinux, firewall state, listening sockets, failed services, and storage encryption visibility in one security overview. Missing information stays unknown.</p><code>systemctl --failed</code><br /><sub>A little light on the services hiding in the shadows.</sub></td>
    <td width="50%" valign="top"><b>↺ RESTORE · A way back</b><p>Restic-powered encrypted backups, snapshot browsing, repository checks, and recovery into a new destination.</p><code>envy gui restore</code><br /><sub>Recovery points for the things worth keeping.</sub></td>
  </tr>
  <tr>
    <td valign="top"><b>◇ VAULT · Keep it yours</b><p>Passphrase-protected file encryption with authenticated encryption and a separate destination for each result.</p><code>envy gui vault</code></td>
    <td valign="top"><b>◌ VEIL · More than meets the eye</b><p>Pack encrypted files and folders into supported image, audio, and video carriers, then unpack them with the right passphrase.</p><code>envy gui veil</code></td>
  </tr>
  <tr>
    <td valign="top"><b>⌁ PURGE · Clear a little space</b><p>Preview old cache files, review what is eligible, and move a selected item to Trash. Deliberate cleanup with a chance to look first.</p><code>du -sh ~/.cache</code><br /><sub>See how much space the dust is taking up.</sub></td>
    <td valign="top"><b>▧ EVIDENCE VAULT · Follow the fingerprints</b><p>Local case manifests, copied-file intake, and hash verification for tracking the integrity of collected files.</p><code>envy gui evidence-vault</code><br /><sub>Integrity checks, with a record to follow.</sub></td>
  </tr>
</table>

<details>
<summary><b>✦ Open the command deck · <code>envy gui command-center</code></b></summary>

### Systems, signals & experiments

| Tool | What I'm building |
| :--- | :--- |
| **⌘ Command Center** | A searchable launch point for the suite, with a system overview, live metrics, and configuration controls. One place to find the next tool. |
| **⌁ Network Lab** | Inspect local interfaces, routing, listening services, and VPN state, then open KDE's connection editor. The spirit of `ip route` with a dedicated control panel. |
| **⚒ Forge** | Rootless Podman image and container management, explicit image pulls, and restricted workspaces for experiments. `podman ps` energy, BLACK VEIL styling. |
| **◈ Oracle** | A local-model interface powered by Ollama, with deliberate model downloads, prompts, and explicit encrypted-history setup. A little oracle in the machine. |
| **▣ Device Center** | Storage identity, PCI drivers, USB, audio, Bluetooth, wireless, and available thermal/GPU readings. Know the hardware behind the glow. |
| **↗ Package Center** | RPM, Flatpak, and container inventories, plus RPM search and interactive installation from configured repositories. `rpm -qa` is only the beginning. |
| **✧ Orbit** | Download orbital elements on request, then predict satellite positions offline with Skyfield. Element age and checksums stay visible. A terminal with its eyes on the stars. |
| **▦ Ops Desk** | Encrypted local plans, role aliases, task assignments, progress, and scheduled check-ins. Save revisions and exchange authenticated handoff files. |

</details>

<p align="center">
  <code>printf '%s\n' 'curiosity → experiments → useful tools'</code><br />
  <sub>The <code>envy gui …</code> commands open tools in an installed BLACK VEIL development environment.</sub>
</p>

<p align="center">
  <sub><b>CURRENT FOCUS</b> &nbsp; Installation · recovery · desktop integration · testing</sub>
</p>


</details>

## ↗ Find me elsewhere

<p align="center">
  <a href="https://linktr.ee/xzchick"><img src="./profile-assets/envy-link-hub.svg" width="430" alt="The Link Hub — find me across the internet" /></a>
</p>

<p align="center">
  <a href="https://www.instagram.com/xzchick"><b>Instagram</b></a> &nbsp; · &nbsp;
  <a href="https://www.tiktok.com/@xzchik"><b>TikTok</b></a> &nbsp; · &nbsp;
  <a href="https://x.com/xzchick"><b>X</b></a> &nbsp; · &nbsp;
  <a href="https://www.twitch.tv/xzchick"><b>Twitch</b></a>
</p>

<p align="center">
  <img src="./profile-assets/envy-signoff.svg" width="100%" alt="Stay a little cosmic" />
</p>




