const { createApp } = Vue;

createApp({
    data() {
        return {
            searchTerm: '',
            operations: [],  // Les opérations seront probablement chargées depuis le backend (par ex., via une requête API).
            showDeleteConfirmation: false,
            operationToDelete: null,
        };
    },
    methods: {
        // Filtre les opérations en fonction du champ de recherche
        filterOperations() {
            return this.operations.filter(operation => 
                operation.card_name.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
                operation.username.toLowerCase().includes(this.searchTerm.toLowerCase())
            );
        },
        // Affiche la boîte de confirmation pour la suppression
        confirmDelete(operation) {
            this.operationToDelete = operation;
            this.showDeleteConfirmation = true;
        },
        // Annule la suppression
        cancelDelete() {
            this.showDeleteConfirmation = false;
            this.operationToDelete = null;
        },
        // Supprime une opération après confirmation
        deleteOperation() {
            if (this.operationToDelete) {
                // Logique pour supprimer l'opération, par exemple, envoyer une requête au backend
                this.operations = this.operations.filter(op => op !== this.operationToDelete);
                this.showDeleteConfirmation = false;
                this.operationToDelete = null;
            }
        }
    },
    mounted() {
        // Chargement simulé des opérations
        this.operations = [
            { id: 1, card_name: 'A23', statut_geo: 'POST-PROD', timestamp: '2024-09-13 14:12:00', username: 'fabt' },
            { id: 2, card_name: 'B66', statut_geo: 'DNA_EQ1', timestamp: '2024-09-12 09:10:00', username: 'john_doe' },
            // Ajoute d'autres opérations fictives ici ou charge depuis l'API
        ];
    }
}).mount('#app');
