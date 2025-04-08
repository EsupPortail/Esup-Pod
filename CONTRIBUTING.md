# Contributing to Esup-Pod

:+1::tada: First off, thanks for taking the time to contribute! :tada::+1:

The following is a set of guidelines for contributing to Pod, which is hosted
in the [Esup Organization](https://github.com/EsupPortail) on GitHub.
These are mostly guidelines, not rules.
Use your best judgment, and feel free to propose changes to this document in a pull request.

## Table of contents

* [Code of Conduct](#code-of-conduct)

* [How Can I Contribute?](#how-can-i-contribute)
  * [Reporting Bugs](#reporting-bugs)
  * [Suggesting Enhancements](#suggesting-enhancements)
  * [Pull Requests](#pull-requests)

* [Styleguides](#styleguides)
  * [Git Commit Messages](#git-commit-messages)

* [Coding conventions](#coding-conventions)
  * [JavaScript Styleguide](#javascript-styleguide)
  * [Python Styleguide](#python-styleguide)

## Code of Conduct

This project and everyone participating in it is governed by the [Pod Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code.
Please report unacceptable behavior to us.

## I don't want to read this whole thing I just have a question

If chat is more your speed, you can [join the Pod team on Rocket chat](https://rocket.esup-portail.org/channel/esup_-_pod).

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report.
Following these guidelines helps maintainers and the
community understand your report :pencil:, reproduce the behavior :computer: :computer:,
and find related reports :mag_right:.

When you are creating a bug report, please [include as many details as possible](#how-do-i-submit-a-good-bug-report).

> **Note:** If you find a **Closed** issue that seems like it is the same thing
that you're experiencing, open a new issue and include a link
to the original issue in the body of your new one.

#### How Do I Submit A (Good) Bug Report?

Bugs are tracked as [GitHub issues](https://guides.github.com/features/issues/).
Create an issue and explain the problem and include additional details
to help maintainers reproduce the problem:

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps which reproduce the problem** in as many details as possible.
* **Provide specific examples to demonstrate the steps**. Include links to files
or GitHub projects, or copy/pasteable snippets, which you use in those examples.
* **Describe the behavior you observed after following the steps** and point out
what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead and why.**
* **Include screenshots and animated GIFs** which show you following the described steps
and clearly demonstrate the problem.
You can use [this tool](https://www.cockos.com/licecap/)
to record GIFs on macOS and Windows,
and [this tool](https://github.com/colinkeenan/silentcast)
or [this tool](https://github.com/GNOME/byzanz) on Linux.
* **If the problem wasn't triggered by a specific action**, describe what you were doing
before the problem happened and share more information using the guidelines below.
* **Can you reliably reproduce the issue?** If not, provide details about
how often the problem happens and under which conditions it normally happens.

Include details about your configuration and environment:

* **Which version of Pod are you using?**
* **What's the name and version of the browser you're using**?

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for Pod,
including completely new features and minor improvements to existing functionality.
Following these guidelines helps maintainers and the community understand
your suggestion :pencil: and find related suggestions :mag_right:.

#### How Do I Submit A (Good) Enhancement Suggestion?

Enhancement suggestions are tracked as [GitHub issues](https://guides.github.com/features/issues/).
Create an issue and provide the following information:

* **Use a clear and descriptive title** for the issue to identify the suggestion.
* **Provide a step-by-step description of the suggested enhancement** as many detailed as possible.
* **Provide specific examples to demonstrate the steps**.
Include copy/pasteable snippets which you use in those examples, as [Markdown code blocks](https://help.github.com/articles/markdown-basics/#multiple-lines).
* **Describe the current behavior**
 and **explain which behavior you expected to see instead** and why.
* **Include screenshots and animated GIFs** which help you demonstrate the steps
or point out the part which the suggestion is related to.
You can use [this tool](https://www.cockos.com/licecap/)
to record GIFs on macOS and Windows,
and [this tool](https://github.com/colinkeenan/silentcast)
or [this tool](https://github.com/GNOME/byzanz) on Linux.
* **Specify which version of Pod you're using.**
* **Specify the name and version of the browser you're using.**

### Pull Requests

The process described here has several goals:

* Maintain quality
* Fix problems that are important to users
* Engage the community in working toward the best possible Pod
* Enable a sustainable system for maintainers to review contributions

Please follow these steps to have your contribution considered by the maintainers:

0. Follow the [styleguides](#styleguides) below.
1. Make sure that your pull request targets the `develop` branch.
2. Prefix the title of your pull request with one of the following:
   * `[WIP]` if your pull request is still a work in progress.
   * `[DONE]` if you are done with your patch.
3. After you submit your pull request, verify that
all [status checks](https://help.github.com/articles/about-status-checks/) are passing

<details>
<summary>What if the status checks are failing?</summary>
If a status check is failing,
and you believe that the failure is unrelated to your change,
please leave a comment on the pull request explaining
why you believe the failure is unrelated.
A maintainer will re-run the status check for you.
If we conclude that the failure was a false positive,
then we will open an issue to track that problem with our status check suite.</details>

While the prerequisites above must be satisfied prior to having your pull request reviewed,
the reviewer(s) may ask you to complete additional design work, tests,
or other changes before your pull request can be ultimately accepted.

## Styleguides

### Git config

Warning about the configuration of line ending: [configuring-git-to-handle-line-endings](https://docs.github.com/fr/get-started/getting-started-with-git/configuring-git-to-handle-line-endings)
We add a .gitattributes file at the root of repository

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to…" not "Moves cursor to…")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
* When only changing documentation, include `[ci skip]` in the commit title
* Consider starting the commit message with an applicable emoji:
  * :art: `:art:` when improving the format/structure of the code
  * :racehorse: `:racehorse:` when improving performance
  * :non-potable_water: `:non-potable_water:` when plugging memory leaks
  * :memo: `:memo:` when writing docs
  * :bug: `:bug:` when fixing a bug
  * :fire: `:fire:` when removing code or files
  * :green_heart: `:green_heart:` when fixing the CI build
  * :white_check_mark: `:white_check_mark:` when adding tests
  * :lock: `:lock:` when dealing with security
  * :arrow_up: `:arrow_up:` when upgrading dependencies
  * :arrow_down: `:arrow_down:` when downgrading dependencies
  * :shirt: `:shirt:` when removing linter warnings

## Coding conventions

Start reading our code and you'll get the hang of it. We optimize for readability:

* Configuration variables are uppercase and can be called
in all modules keeping the same name.
For example, `MAVAR = getattr(settings, "MAVAR", default value)`
* Global variables to a module are also in uppercase but are considered private
to the module and therefore must be prefixed and suffixed with a double underscore
* All .py files must be indented using **4 spaces**,
and all other files (.css, .html, .js) with **2 spaces** (soft tabs)
* This is open source software.
Consider the people who will read your code, and make it look nice for them.
It's sort of like driving a car: Perhaps you love doing donuts when you're alone,
but with passengers the goal is to make the ride as smooth as possible.

### JavaScript Styleguide

All JavaScript code is linted with [eslint](https://eslint.org/).

### Python Styleguide

All python code is linted with [flake8](https://flake8.pycqa.org/en/latest/)

### Typography

Please use these typographic characters in all displayed strings:

* Use Apostrophe (’) instead of single quote (')
  * English samples: don’t, it’s
  * French samples: J’aime, l’histoire
* Use the ellipsis (…) instead of 3 dots (...)
  * English sample: Loading…
  * French sample: Chargement…
* Use typographic quotes (“ ”) instead of neutral quotes (" ")
  * English sample: You can use the “Description” field below.
  * French sample: Utilisez le champ « Description » ci-dessous
