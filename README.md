<div id="top"></div>

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/github_username/repo_name">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">forNMA</h3>

  <p align="center">
    forNMA was designed to analyze and integrate data from single-cell time-lapse microscopy, performing Nuclear Morphometric Analysis, translocation measurements and nuclear foci counting.
    <br />
    <a href="https://github.com/github_username/repo_name"><strong>How to use »</strong></a>
    <br />
    <br />
    <a href="https://github.com/github_username/repo_name">View Demo</a>
    ·
    <a href="https://github.com/github_username/repo_name/issues">Report Bug</a>
    ·
    <a href="https://github.com/github_username/repo_name/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <ul>
        <li><a href="#image-registration">Image Registration</a></li>
        <li><a href="#segmentation-and-feature-extraction">Segmentation and feature extraction</a></li>
        <li><a href="#filter-results">Filter Results</a></li>
        <li><a href="#tracking">Tracking</a></li>
    </ul>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About forNMA

[![Product Name Screen Shot][product-screenshot]](https://example.com)

forNMA came to simplify single-cell microscopy analysis in a single pipeline. It accepts as input raw  2D muti-channel images and is divided in two main steps, the Processing and Analysis.
The processing step has four different modules: Registration, Segmentation, Correction and Cell Tracking. 
 * The Registration module corrects microscope movements along time axis in all separate image channels. 
 * Segmentation module comprises a complex pipeline of classic computer vision approaches to better find nuclei contours. It can also be performed with the  deep learning-based segmentation method, Cellpose. In this stpe all nuclear features are measured.
 * The the Correction module removes wrongly detected nuclei with user selected parametes. 
 * Cell Tracking module links cells trough time frames based on their X and Y positions in the final DataFrame. 

In the Analysis step, user can use forNMA iterative interface to plot all data generated, including [NMA](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0042522) plots integrating different cellular characteristics. Here user can also generate videos of tracked cells and perform nuclear foci overlapping. 

<p align="right">(<a href="#top">back to top</a>)</p>



### Built With

* [Next.js](https://nextjs.org/)
* [React.js](https://reactjs.org/)
* [Vue.js](https://vuejs.org/)
* [Angular](https://angular.io/)
* [Svelte](https://svelte.dev/)
* [Laravel](https://laravel.com)
* [Bootstrap](https://getbootstrap.com)
* [JQuery](https://jquery.com)

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* npm
  ```sh
  npm install npm@latest -g
  ```

### Installation

1. Get a free API Key at [https://example.com](https://example.com)
2. Clone the repo
   ```sh
   git clone https://github.com/github_username/repo_name.git
   ```
3. Install NPM packages
   ```sh
   npm install
   ```
4. Enter your API in `config.js`
   ```js
   const API_KEY = 'ENTER YOUR API';
   ```

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage
For information about forNMA parameters, interface usage and frequently asked questions, see the documentation at [Labsinal](https://nextjs.org/).
forNMA also has a headless mode, and each module can be called independently as follows:

### Image Registration
 ```sh
   fornma registration path_list path_to_save --crop
   ```
 Where:
 * path_list is a list where each item is a path to a folder containing all images to be registered in one channel. Every folder in the list wil be registered against each other too; 
 * path_to_save is the path where registered images will be saved;
 * -- crop is a boolean. If True, all images will be cropped to keep only the field that remains in view.

### Segmentation and Feature Extraction
```sh
   fornma run parameters --headless
  ```
   Where:
 * parameters is the path to the parameters.toml file; 
 * -- headless is true when running without any GUI.
 
 Here you find more infromation on how to use [TOML](https://toml.io/en/) and how to [set parameters](ufrgs.br/labsinal).

### Filter Results 
Here write about filering function

### Tracking
```sh
   fornma tracking path_to_table path_to_save -md -t -ms -mg -am
  ```
  Where:
 * path_to_table is the path to forNMA results CSV file;
 * path_to_save is the path where tracked CSV will be saved;
 * -md, --max_distance is the maximal distance to allow particle linking between frames;
 * -t, --time_window is the maximal memory of the tracker to link track segments;
 * -ms, --max_split_distanceis the maximal distance to link segment starts to segment middlepoints;
 * -mg, --max_gap_closing_distance is the maximal distance for closing segment gaps;
 * -am, --allow_merging indicates whether object merging is allowed or not.
 
Notice that optional arguments must be optimized for every experimental condition, and default values are just a suggestion.

#### Draw Tracking at Images
```sh
   fornma draw_tracking path_to_table path_to_images path_to_save -rs
  ```
  Where:
 * path_to_table is the path to forNMA tracking results CSV file;
 * path_to_images is the path to a folder containing images to be drawn;
 * path_to_save is the path where images will be saved;
 * -rs, --rescale_intesity indicates whether image intensities must be rescaled.



<p align="right">(<a href="#top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3
    - [ ] Nested Feature

See the [open issues](https://github.com/github_username/repo_name/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Your Name - [@twitter_handle](https://twitter.com/twitter_handle) - email@email_client.com

Project Link: [https://github.com/github_username/repo_name](https://github.com/github_username/repo_name)

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* []()
* []()
* []()

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/github_username/repo_name.svg?style=for-the-badge
[contributors-url]: https://github.com/github_username/repo_name/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/github_username/repo_name.svg?style=for-the-badge
[forks-url]: https://github.com/github_username/repo_name/network/members
[stars-shield]: https://img.shields.io/github/stars/github_username/repo_name.svg?style=for-the-badge
[stars-url]: https://github.com/github_username/repo_name/stargazers
[issues-shield]: https://img.shields.io/github/issues/github_username/repo_name.svg?style=for-the-badge
[issues-url]: https://github.com/github_username/repo_name/issues
[license-shield]: https://img.shields.io/github/license/github_username/repo_name.svg?style=for-the-badge
[license-url]: https://github.com/github_username/repo_name/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username
[product-screenshot]: images/screenshot.png
