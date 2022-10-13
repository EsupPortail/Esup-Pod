function isFooterInView() {
    var footer = document.querySelector('footer.container-fluid.pod-footer-container');
    var rect = footer.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)

    );
}  

//chech if user scrolled to

class InfiniteLoader{
    constructor(getData){
        this.page = 1;
        window.addEventListener('load', (e) => {this.initMore(getData)} );
        window.addEventListener('scroll', (e) => { ;this.initMore(getData)});
        

    }

    initMore(getData){
        if (isFooterInView()) {
            getData(this.page);
            console.log(this.page)
            this.page += 1;
           
        }
    }
   

}


