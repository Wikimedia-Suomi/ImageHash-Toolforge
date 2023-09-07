var app = Vue.component('app', {
    data: function() {
        return {
            filename: '',
            results: []
        }
    },
    methods: {
        search: function() {
            fetch(`https://imagehash.toolforge.org/pagesearch?page_title=${this.filename}`)
                .then(response => response.json())
                .then(data => {
                    this.results = data;
                });
        }
    },
    template: `
        <div>
            <input type="text" v-model="filename" placeholder="Enter filename">
            <button @click="search">Search</button>
            
            <div v-for="result in results" :key="result.page_id">
                <img :src="result.thumbnail" :alt="result.page_title">
            </div>
        </div>
    `
});

