// posts/posts.11tydata.js
module.exports = {
    // Set the default layout for all files in this directory
    // We already have it in front matter, but this is good practice
    layout: "post.njk",
  
    // Define the permalink structure
    // Input: ./posts/my-cool-post.md
    // Output: /my-cool-post/index.html (URL: /my-cool-post/)
    permalink: "/{{ page.fileSlug }}/"
  };