'use strict';

const gulp = require("gulp"),
      fs = require('fs'),
      sass = require("gulp-sass"),
      sassLint = require('gulp-sass-lint'),
      clean = require('gulp-clean'),
      rename = require("gulp-rename"),
      data = require("gulp-data"),
      nunjucks = require('gulp-nunjucks');

// set paths ...
const config = {
  scssPath: "src/scss",
  jsDestPath: "application/static/javascripts",
  destPath: "application/static/stylesheets",
  govukAssetPath: "application/static/govuk-frontend/assets",
  chromeExtDest: "extensions/chrome/",
  chromeExtStaticDest: "extensions/chrome/popup/static"
}


// Tasks used to generate latest stylesheets
// =========================================
const cleanCSS = () =>
  gulp
    .src('application/static/stylesheets/**/*', {read: false})
    .pipe(clean());
cleanCSS.description = `Delete old stylesheets files`;

// compile scss to CSS
const compileStylesheets = () =>
  gulp
    .src( config.scssPath + '/*.scss')
	  .pipe(sass({outputStyle: 'expanded',
		  includePaths: [ 'src/scss', 'src/govuk-frontend']}))
      .on('error', sass.logError)
    .pipe(gulp.dest(config.destPath));

// check .scss files against .sass-lint.yml config
const lintSCSS = () =>
  gulp
    .src('src/scss/**/*.s+(a|c)ss')
    .pipe(sassLint({
      files: {ignore: 'src/scss/styleguide/_highlight-style.scss'},
      configFile: '.sass-lint.yml'
    }))
    .pipe(sassLint.format())
    .pipe(sassLint.failOnError());


// Tasks for copying assets to application
// ======================================
const copyVendorStylesheets = () =>
  gulp
    .src('src/stylesheets/**/*')
    .pipe(gulp.dest(config.destPath));

const copyGovukAssets = () =>
  gulp
    .src('src/govuk-frontend/assets/**/*')
    .pipe(gulp.dest(config.govukAssetPath));

const copyJS = () =>
  gulp
    .src('src/js/**/*.js')
    .pipe(gulp.dest(`${config.jsDestPath}`));

const copyCompiledCSS = () =>
  gulp
    .src([`${config.destPath}/dl-frontend.css`, `${config.destPath}/popup.css`])
    .pipe(gulp.dest(`${config.chromeExtStaticDest}`));


// Generate extension popup
// ========================
const generateExtensionPopup = () =>
  gulp
    .src("application/templates/browser-ext-popup.html")
    .pipe(data(getDataForExtTemplate))
    .pipe(nunjucks.compile('.', {}))
    .pipe(rename("popup.html"))
    .pipe(gulp.dest(`${config.chromeExtDest}`));

function getDataForExtTemplate(file) {
  var fact_type_json = 'data/fact-types.json';
  var fact_types = null;
  if(fs.existsSync(fact_type_json)) {
    fact_types = JSON.parse(fs.readFileSync(fact_type_json, "utf8"));
  }
  //console.log(fact_types);
  return {
    fact_types: fact_types
  }
}

// Tasks to expose to CLI
// ======================
const copyAllAssets = gulp.parallel(
  copyVendorStylesheets,
  copyGovukAssets,
  copyJS
);
copyAllAssets.description = `Copy all vendor and 3rd party assets to application`;

const latestStylesheets = gulp.series(
  cleanCSS,
  compileStylesheets,
  gulp.parallel(
    copyVendorStylesheets,
    copyGovukAssets,
    copyCompiledCSS
  )
);
latestStylesheets.description = `Generate the latest stylesheets`;

// Watch for scss changes
const watch = () => gulp.watch("src/scss/**/*", latestStylesheets);
watch.description = `Watch all project .scss for changes, then rebuild stylesheets.`;

// Set watch as default task
exports.default = watch;
exports.stylesheets = latestStylesheets;
exports.copyAssets = copyAllAssets;
exports.generatePopup = generateExtensionPopup;
