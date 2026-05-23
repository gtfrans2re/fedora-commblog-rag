# Article guidelines

> Looking for how to write an article? See [this page](#)!

---

The Community Blog is one of the most important platforms for how information and news about the Fedora community, for the Fedora community, is shared.

There are a few guidelines and important steps to consider when writing and reviewing articles to be published on the Community Blog. Following these steps will help keep the Community Blog organized and easy to navigate, and help boost things like search engine optimization (SEO) and accessibility of content.

If you are reviewing an article, follow these checks and guidelines to help prepare an article for publication.

---

# For writers and editors

## Content

- **Put the important takeaway information in the first paragraph.**  
  Don’t assume the reader will read the whole post.

---

## Formatting

- **Remove all HTML tags from your post except for headings, bold / emphasis formatting, hyperlinks, and tables.**  
  WordPress doesn’t show advanced kinds of HTML well. It helps the review process if the article is clean from tags that may be added by other blogging or publishing platforms.

- **Insert a “Read More” divider.**  
  This keeps the front page compact. It generally fits best after the first paragraph. It also helps bring readers to the Community Blog itself when some websites or blogs “reblog” or reshare our content.

### Images

- Images should have a relevant caption and alt tag.

- Be sure to provide the proper attribution for images as required by the license.  
  If you are unclear of the license or the attribution requirements, file a ticket with the CommOps team to discuss it.

- Upload images to WordPress.  
  Do not “hotlink” to images hosted elsewhere.

- You may use as many images as you need, but keep in mind that some readers may be on low-bandwidth or metered connections.  
  *Do not include your featured image in the body of the post.*

### Headers

- **Use headers for longer articles.**  
  “Longer” is roughly 400 words or more.

- **Use important keywords in headers.**  
  Search engines use headers to help filter and find relevant pages for searches.

- **Use lists where they improve readability.**  
  Lists can be easier to read than long paragraphs. Use unordered lists unless the sequence of steps matters.

- **Use blockquotes for long quotes.**  
  This improves readability.

- **Don’t use “here” as text for links.**  
  This is bad for accessibility and SEO.

---

## Metadata

- **Add the appropriate category.**  
  Posts should have a single Category, except for events-related posts, which should have `Events` in addition to the topical category.

  If your post is about a Fedora Activity Day for the Design Team, you would use the `Design` and `Events` categories.

  The *Fedora Project Community* is a default category and should be used sparingly.

  If a new category needs to be added, file a ticket with the CommOps team to discuss it.

- **Add appropriate tags.**  
  You are free to add any tags you wish, but a good number is between 3–6 per article.

  The tag UI window will suggest tags as you type. Avoid creating new tags when possible.

  If you do create new tags:

  - Follow proper capitalization rules where possible.

  - Think strategically.  
    Think of keywords that are important about the article. The tags are a helpful tool for SEO to make your article pop out more.

    Using `development` isn’t a good keyword because it’s generic, but using `Anaconda` or `Diversity and inclusion` are better. They highlight the critical points of your article.

- **Add a featured image (optional).**

  Having a hard time finding a suitable picture? Unsplash has a large library of images released in the public domain that you can choose from — just try to keep it related to what you’re writing about!

  If you need help finding a picture, we can help design a featured image for your post.

  *Do not include the featured image in the body of your post.*

  If you create a featured image, send it as a pull request to the Fedora Community Blog images repo on Pagure.

  - Use the title of the article in the featured image alt tag.  
    This provides an SEO boost.

---

# For Editors

- **Ensure the author has a Discourse user name set in their profile.**  
  This will be their Fedora Account ID.

  It is necessary for the Discourse topic to have the right user name. Edit the user and fill in the box toward the bottom of the profile page.

  - If the post publishes with the `system` Discourse user, a Discourse admin can change the owner after the fact.

---

# SEO Plugin

The Community Blog doesn’t use many plugins for WordPress and it’s unlikely you’ll need to use many other than one: **Yoast SEO**.

The Yoast SEO plugin is a helpful tool that gives you live feedback on your article and provides tips for finding ways to improve your article.

You can find it towards the bottom of every article, after the main article text box ends.

Since this is the only plugin editors will need to interact with most of the time, it will be the only plugin covered in these guidelines.

- **Set a focus keyword.**  
  Use one specific word or phrase. Using multiple keywords will throw off the algorithm.

  This is not necessary for regular updates.

- **Set the article snippet.**  
  This is the text that will show up with the article when posted to social media websites or other platforms.

  - Use the focus keyword in the snippet.  
    This is a significant boost for SEO and helps make the article more discoverable.

- Generally, resolving the red-bubble suggestions is helpful, but don’t feel like you have to resolve them all.

  If it doesn’t feel like it makes sense or you will have to drastically revise the article, don’t worry about it.

  The Community Blog isn’t focused on an external audience and is mostly for contributors.

  It’s better to get the big points right and ship it soon.

---

# Scheduling

- **Try to publish no more than one article per day.**  
  Publishing more than one article reduces the total number of views for both articles.

  For urgent topics, like an upcoming test day or another announcement, you need to do it.

  But when possible, try to avoid double-publishing because it will cut the impact of both articles published.

- **Aim for Tuesdays and Thursdays.**  
  These dates balance against the Fedora Magazine, which normally publishes on Mondays, Wednesdays, and Fridays.

- **Share content that might be interesting to a wider audience (e.g. users) with the Social Media team.**  
  The best way to do this is to send a link to the social-media mailing list.

  Writing a subject line and dropping a link is all you have to do.

- **Add the post to the calendar on Discourse.**  
  The Discourse thread has a calendar for upcoming posts.

  If you need to move a post to accommodate a time-sensitive post, make sure you update the schedule date in WordPress and edit the corresponding schedule thread post.

---

# Issues with the theme / design

If you notice issues or problems with the theme / design for the Community Blog, there is a Pagure repo for the theme.

Ryan Lerch is the designer for the Community Blog theme and is the best point of contact for getting support with the theme.

---

*Updated: 2022-01-20*
