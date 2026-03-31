# Wildlife Tag

I have over 8000 shots of animals and rather than spending ages trying to identify them so I can find pictures of lions or owls I wanted to get some ML going to do the work for me.

## The pipeline

- Create a jpg preview of each file in a subfolder using  [ImageMagick](https://imagemagick.org/#gsc.tab=0)
as most ML tools can't read native raw files

- Use Yolo9 to find the animal in the picture
- pass that to iNaturlaist to identify the species
- create a naturlist like hierarchy. For example Lions are Cats, and owls are a type of Raptor which is of the family of birds. This way I* can find all catsd birds etc as well as dig into the specifi species like Tawny Owl.
- Call **ExifTool** (pyexiftool package) to add the discovered tags to an xmp metadata file alongside the raw file as raw files can't store this sort of metadata

## Notes

- The powershell sript wildlife_tag.ps1 takes a path as an argument so it can be tested against a small sample in a designmated folder structure
- XMP files may alrady exist with data about the raw file so this projects will call **ExifTool** to gracefully add tags to a specific namespace

``` XMP-wildlife:Species
XMP-wildlife:Confidence
XMP-wildlife:ModelVersion
XMP-wildlife:Detector
XMP-wildlife:Classifier
```

The script provides a `-test` switch that enables a non-destructive diagnostic mode. When enabled, the script behaves identically to normal execution but additionally creates a timestamped CSV log file under `output/preview_log_YYYYMMDD_HHMMSS.csv`
